// Marca CantinAPP: ilustración en un marco de boceto + nombre.
const SIZES = {
  sm: { box: 'h-10 w-10', text: 'text-2xl' },
  md: { box: 'h-14 w-14', text: 'text-3xl' },
  lg: { box: 'h-16 w-16', text: 'text-4xl' },
}

export default function Logo({ size = 'md', as: Title = 'span' }) {
  const s = SIZES[size]
  return (
    <div className="flex items-center gap-3">
      <span className={`surface grid shrink-0 place-items-center overflow-hidden bg-white p-1 ${s.box}`}>
        <img src="/logo.webp" alt="" className="h-full w-full object-contain" />
      </span>
      <Title className={`mt-1 font-display font-bold tracking-tight text-ink ${s.text}`}>CantinAPP</Title>
    </div>
  )
}
