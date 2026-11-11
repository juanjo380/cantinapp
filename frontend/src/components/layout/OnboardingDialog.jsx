import WavingHandIcon from "@mui/icons-material/WavingHandOutlined";
import { useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Bottle, Star, Sun } from "../auth/AuthShell";
import FormDialog from "../ui/FormDialog";

// Flecha con rizo (una sola curva cúbica que se cruza consigo misma) del modal hacia el destino.
function swirlPath(start, end) {
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  const nx = -dy * 0.45;
  const ny = dx * 0.45;
  const c1 = { x: start.x + dx * 1.35 + nx, y: start.y + dy * 1.35 + ny };
  const c2 = { x: start.x - dx * 0.35 + nx, y: start.y - dy * 0.35 + ny };
  return `M ${start.x} ${start.y} C ${c1.x} ${c1.y} ${c2.x} ${c2.y} ${end.x} ${end.y}`;
}

function useArrow(anchorRef, getTarget) {
  const [geometry, setGeometry] = useState(null);
  useLayoutEffect(() => {
    function measure() {
      const target = getTarget();
      const anchor = anchorRef.current;
      if (!target || !anchor) return setGeometry(null);
      const t = target.getBoundingClientRect();
      const a = anchor.getBoundingClientRect();
      const below = t.top < a.top; // en móvil el destino (menú) queda arriba del modal
      setGeometry({
        target: t,
        start: below
          ? { x: a.left + 24, y: a.top - 8 }
          : { x: a.left - 12, y: a.top + a.height / 2 },
        end: below
          ? { x: t.left + t.width / 2, y: t.bottom + 14 }
          : { x: t.right + 14, y: t.top + t.height / 2 },
      });
    }
    const frame = requestAnimationFrame(measure); // espera a que el modal esté montado
    window.addEventListener("resize", measure);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("resize", measure);
    };
  }, [anchorRef, getTarget]);
  return geometry;
}

// Bienvenida tras el registro: señala con una flecha el bloque «Negocio» de la barra lateral.
export default function OnboardingDialog({ getTarget, onClose, onStart }) {
  const anchorRef = useRef(null);
  const arrow = useArrow(anchorRef, getTarget);

  return (
    <>
      <FormDialog
        title="¡Bienvenido a CantinAPP!"
        icon={<WavingHandIcon />}
        onClose={onClose}
        onSubmit={onStart}
        submitLabel="Completar ahora"
        cancelLabel="Más tarde"
        decor={
          <>
            <Bottle className="pointer-events-none absolute bottom-3 left-4 h-14 w-10" />
            <Sun className="pointer-events-none absolute bottom-3 left-14 h-14 w-14" />
            <Star className="pointer-events-none absolute bottom-10 left-28 h-6 w-6" />
          </>
        }
      >
        <div
          ref={anchorRef}
          className="flex flex-col gap-3 text-sm text-ink-soft"
        >
          <p>
            Tu negocio ya está creado. Antes de empezar, completa{" "}
            <strong className="text-ink">el perfil</strong> en el apartado{" "}
            <strong className="text-ink">Negocio</strong> que te señalamos:
          </p>
          <ul className="list-disc pl-5">
            <li>tus datos: nombre, cargo y teléfono;</li>
            <li>los del negocio: tipo, NIT, dirección, ciudad y contacto;</li>
            <li>tus sedes y las personas de tu equipo.</li>
          </ul>
          <p>
            Cuando lo completes, verás el nombre de tu negocio en ese lugar.
          </p>
        </div>
      </FormDialog>

      {arrow &&
        createPortal(
          <svg
            className="pointer-events-none fixed inset-0 z-[1400] h-full w-full"
            aria-hidden="true"
          >
            <defs>
              <marker
                id="onboarding-head"
                viewBox="0 0 10 10"
                refX="7"
                refY="5"
                markerWidth="7"
                markerHeight="7"
                orient="auto"
              >
                <path
                  d="M 0 0 L 10 5 L 0 10"
                  fill="none"
                  stroke="var(--brand)"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              </marker>
            </defs>
            <path
              d={swirlPath(arrow.start, arrow.end)}
              pathLength="1"
              className="draw-in"
              fill="none"
              stroke="var(--brand)"
              strokeWidth="3"
              strokeLinecap="round"
              markerEnd="url(#onboarding-head)"
            />
            <ellipse
              cx={arrow.target.left + arrow.target.width / 2}
              cy={arrow.target.top + arrow.target.height / 2}
              rx={arrow.target.width / 2 + 12}
              ry={arrow.target.height / 2 + 10}
              transform={`rotate(-3 ${arrow.target.left + arrow.target.width / 2} ${arrow.target.top + arrow.target.height / 2})`}
              fill="none"
              stroke="var(--sun)"
              strokeWidth="3"
              strokeDasharray="10 6"
            />
          </svg>,
          document.body,
        )}
    </>
  );
}
