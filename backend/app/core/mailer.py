"""Envío de correos y sus plantillas. Con MAIL_BACKEND=console el correo solo se escribe
en el log (en development con el contenido, para poder copiar los códigos)."""
import asyncio
import json
import logging
import urllib.error
import urllib.request
from html import escape

from app.core.config import get_settings
from app.core.exceptions import AppError

logger = logging.getLogger("cantinapp.mail")
_BREVO_URL = "https://api.brevo.com/v3/smtp/email"


class MailError(AppError):
    status_code = 503


def _post_brevo(api_key: str, payload: dict) -> None:
    request = urllib.request.Request(
        _BREVO_URL,
        data=json.dumps(payload).encode(),
        headers={"api-key": api_key, "content-type": "application/json", "accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        response.read()


async def send_email(to: str, subject: str, text: str, html: str, *, quiet: bool = False) -> None:
    """`quiet`: avisos que no deben tumbar la operación si el correo falla."""
    settings = get_settings()
    if settings.mail_backend == "console":
        body = text if settings.environment == "development" else "(contenido oculto fuera de development)"
        logger.warning("Correo NO enviado (MAIL_BACKEND=console) a %s: %s\n%s", to, subject, body)
        return
    payload = {
        "sender": {"name": settings.mail_from_name, "email": settings.mail_from},
        "to": [{"email": to}],
        "subject": subject,
        "textContent": text,
        "htmlContent": html,
    }
    try:
        await asyncio.to_thread(_post_brevo, settings.brevo_api_key.get_secret_value(), payload)
    except Exception as exc:  # noqa: BLE001 - red, HTTP 4xx/5xx de Brevo, timeout
        # Nunca str(exc) a secas: algunos errores de urllib incluyen el valor de la cabecera api-key.
        if isinstance(exc, urllib.error.HTTPError):
            detail = f"HTTP {exc.code}: {exc.read()[:300]!r}"
        else:
            detail = type(exc).__name__
        logger.error("No se pudo enviar el correo a %s (%s): %s", to, subject, detail)
        if not quiet:
            raise MailError("No pudimos enviar el correo. Inténtalo de nuevo en unos minutos.") from exc


# --- Plantillas -----------------------------------------------------------------
# Todo dato que escribe un usuario (nombres de negocio o de persona) pasa por escape():
# así nadie puede meter HTML o enlaces falsos en un correo que firma CantinAPP.

def _html(heading: str, paragraphs: list[str], code: str | None = None, button: tuple[str, str] | None = None) -> str:
    parts = [f'<h2 style="margin:0 0 16px;color:#1c1917">{escape(heading)}</h2>']
    parts += [f'<p style="margin:0 0 12px;line-height:1.5">{escape(p)}</p>' for p in paragraphs]
    if code:
        parts.append(
            '<p style="margin:16px 0;font-size:32px;font-weight:700;letter-spacing:8px;'
            f'font-family:monospace;color:#c2410c">{escape(code)}</p>'
        )
    if button:
        label, url = button
        parts.append(
            f'<p style="margin:20px 0"><a href="{escape(url)}" style="background:#f97316;color:#1c1917;'
            'padding:12px 20px;border-radius:8px;text-decoration:none;font-weight:700">'
            f"{escape(label)}</a></p>"
            f'<p style="font-size:12px;color:#57534e">Si el botón no abre, copia este enlace: {escape(url)}</p>'
        )
    parts.append('<p style="margin-top:24px;font-size:12px;color:#57534e">CantinAPP · Este correo es automático.</p>')
    return f'<div style="font-family:Arial,sans-serif;max-width:520px;color:#292524">{"".join(parts)}</div>'


def password_reset_email(code: str, minutes: int) -> tuple[str, str, str]:
    lines = [
        "Recibimos una solicitud para cambiar la contraseña de tu cuenta de CantinAPP.",
        f"Escribe este código en la aplicación. Vence en {minutes} minutos y solo sirve una vez.",
        "Si no fuiste tú, ignora este correo: tu contraseña sigue igual.",
    ]
    text = f"{lines[0]}\n\nCódigo: {code}\n\n{lines[1]}\n{lines[2]}"
    return "Tu código para cambiar la contraseña", text, _html("Cambia tu contraseña", lines, code=code)


def password_changed_email() -> tuple[str, str, str]:
    lines = [
        "La contraseña de tu cuenta de CantinAPP acaba de cambiar y cerramos las demás sesiones abiertas.",
        "Si no fuiste tú, recupera tu cuenta ya desde «¿Olvidaste tu contraseña?» en la pantalla de inicio.",
    ]
    return "Tu contraseña cambió", "\n\n".join(lines), _html("Tu contraseña cambió", lines)


def invitation_email(business: str, role: str, inviter: str, link: str, hours: int) -> tuple[str, str, str]:
    lines = [
        f"{inviter} te invitó a unirte a «{business}» en CantinAPP como {role}.",
        "Abre el enlace con la cuenta de este correo. Te pediremos un código de seguridad de 6 dígitos: "
        "te lo da directamente la persona que te invitó, no viene en este correo.",
        f"La invitación vence en {hours} horas. Si no conoces a quien te invita, ignora este correo.",
    ]
    text = "\n\n".join([lines[0], f"Aceptar: {link}", *lines[1:]])
    html = _html("Te invitaron a un negocio", lines, button=("Ver invitación", link))
    return f"Invitación a {business} en CantinAPP", text, html


def alerts_digest_email(business: str, items: list[tuple[str, int, int, int | None]], link: str) -> tuple[str, str, str]:
    """Resumen diario. `items`: (producto, stock actual, stock mínimo, cantidad sugerida o None)."""
    def line(name: str, stock: int, minimum: int, suggested: int | None) -> str:
        state = "agotado" if stock <= 0 else f"quedan {stock} (mínimo {minimum})"
        return f"{name}: {state}" + (f"; sugerimos comprar {suggested}" if suggested else "")

    lines = [line(*item) for item in items]
    count = len(items)
    intro = (
        f"Hoy {'hay 1 producto' if count == 1 else f'hay {count} productos'} de «{business}» con poco stock "
        "o agotados:"
    )
    text = "\n".join([intro, "", *[f"- {item}" for item in lines], "", f"Revísalos en CantinAPP: {link}"])
    html = _html("Productos por reabastecer", [intro, *lines], button=("Ver alertas", link))
    return f"{business}: {count} producto{'s' if count != 1 else ''} por reabastecer", text, html
