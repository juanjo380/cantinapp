import Logo from '../ui/Logo'

// Ilustraciones naive del fondo; usan los tokens para adaptarse al tema oscuro.
function Decorations() {
  const ink = 'var(--edge)'
  return (
    <>
      <svg className="pointer-events-none absolute inset-0 h-full w-full" aria-hidden="true" preserveAspectRatio="none" viewBox="0 0 1000 800">
        <path d="M0 720 Q 60 690 120 720 T 240 720 T 360 720 T 480 720 T 600 720 T 720 720 T 840 720 T 960 720 T 1080 720" fill="none" stroke={ink} strokeWidth="2.5" strokeLinecap="round" opacity="0.5" />
        <path d="M0 750 Q 60 725 120 750 T 240 750 T 360 750 T 480 750 T 600 750 T 720 750 T 840 750 T 960 750 T 1080 750" fill="none" stroke="var(--brand)" strokeWidth="3" strokeLinecap="round" opacity="0.6" />
        <g fill={ink} opacity="0.25">
          {[[90, 120], [110, 150], [85, 170], [900, 90], [920, 115], [880, 130], [860, 620], [880, 645], [130, 580], [150, 605]].map(([cx, cy]) => (
            <circle key={`${cx}-${cy}`} cx={cx} cy={cy} r="3" />
          ))}
        </g>
      </svg>

      <Sun className="float-slow absolute top-10 right-10 hidden h-28 w-28 md:block" />
      <Cloud className="float-fast absolute top-24 left-10 hidden h-20 w-36 md:block" />
      <Bottle className="float-slow absolute bottom-20 left-8 hidden h-28 w-20 lg:block" />
      <Star className="float-fast absolute right-12 bottom-24 hidden h-16 w-16 lg:block" />
    </>
  )
}

// Figuras sueltas: también decoran las esquinas de los modales legales del registro.
const INK = 'var(--edge)'

export function Sun({ className }) {
  return (
    <svg className={className} viewBox="0 0 120 120" aria-hidden="true">
      <g className="spin-slow">
        <path d="M60 8 L66 30 M60 112 L66 90 M8 60 L30 54 M112 60 L90 66 M22 22 L38 38 M98 98 L82 82 M98 22 L82 38 M22 98 L38 82" stroke="var(--brand)" strokeWidth="4" strokeLinecap="round" fill="none" />
      </g>
      <circle cx="60" cy="60" r="26" fill="var(--sun)" stroke={INK} strokeWidth="2.5" />
      <circle cx="52" cy="56" r="2.5" fill="#1c1917" />
      <circle cx="68" cy="56" r="2.5" fill="#1c1917" />
      <path d="M50 66 Q60 74 70 66" fill="none" stroke="#1c1917" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  )
}

export function Cloud({ className }) {
  return (
    <svg className={className} viewBox="0 0 160 80" aria-hidden="true">
      <path d="M30 60 Q10 60 14 44 Q18 30 36 34 Q40 16 62 20 Q78 6 96 22 Q120 16 124 38 Q146 38 142 56 Q138 62 120 62 Z" fill="var(--panel)" stroke={INK} strokeWidth="2.5" strokeLinejoin="round" />
    </svg>
  )
}

export function Bottle({ className }) {
  return (
    <svg className={className} viewBox="0 0 80 110" aria-hidden="true">
      <path d="M20 10 L60 10 L56 40 Q70 50 66 80 Q62 100 40 100 Q18 100 14 80 Q10 50 24 40 Z" fill="var(--brand-tint)" stroke={INK} strokeWidth="2.5" strokeLinejoin="round" />
      <path d="M22 60 Q40 56 58 60 L60 74 Q40 78 20 74 Z" fill="var(--brand)" opacity="0.85" />
      <path d="M30 20 L32 34" stroke={INK} strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

export function Star({ className }) {
  return (
    <svg className={className} viewBox="0 0 60 60" aria-hidden="true">
      <path d="M30 4 L36 22 L55 24 L40 36 L46 56 L30 44 L14 56 L20 36 L5 24 L24 22 Z" fill="var(--sun)" stroke={INK} strokeWidth="2.5" strokeLinejoin="round" />
    </svg>
  )
}

// `wide`: tarjeta más ancha y espaciado compacto para que el registro quepa sin scroll en ~650 px de alto.
export default function AuthShell({ title, subtitle, children, footer, wide = false }) {
  return (
    <main
      className={`relative flex min-h-svh flex-col items-center justify-center overflow-hidden bg-ground ${
        wide ? 'px-6 py-4' : 'p-6'
      }`}
    >
      <Decorations />
      <div className={`relative z-10 w-full ${wide ? 'max-w-xl' : 'max-w-md'}`}>
        <div className={`flex justify-center ${wide ? 'mb-5' : 'mb-8'}`}>
          <Logo size={wide ? 'md' : 'lg'} />
        </div>
        <div className={`surface ${wide ? 'p-6 md:p-8' : 'p-8 md:p-10'}`}>
          <h1 className="mb-2 text-3xl text-ink">{title}</h1>
          <p className="text-sm font-medium text-ink-soft">{subtitle}</p>
          <div className={wide ? 'mt-5' : 'mt-6'}>{children}</div>
        </div>
        {footer && (
          <div className={`text-center text-sm font-medium text-ink-soft ${wide ? 'mt-4' : 'mt-6'}`}>{footer}</div>
        )}
      </div>
    </main>
  )
}
