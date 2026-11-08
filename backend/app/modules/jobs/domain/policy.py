"""Reglas del trabajo diario (lógica pura)."""
from datetime import datetime


def should_send_digest(new_alerts: list, last_sent: datetime | None, now: datetime) -> bool:
    """Un solo correo al día por negocio, y solo si hay alertas que aún no se avisaron.

    El día se compara en la zona de `now` (UTC en el job): llamar dos veces el mismo día no repite el correo.
    """
    if not new_alerts:
        return False
    return last_sent is None or last_sent.astimezone(now.tzinfo).date() < now.date()
