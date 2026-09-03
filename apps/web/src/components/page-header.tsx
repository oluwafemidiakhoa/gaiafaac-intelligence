export function PageHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string
  title: string
  description: string
}) {
  return (
    <header className="max-w-4xl">
      <div className="border-primary/15 bg-primary/[0.06] inline-flex items-center gap-2 rounded-full border px-3 py-1.5">
        <span className="bg-primary size-1.5 rounded-full shadow-[0_0_10px_color-mix(in_oklab,var(--primary)_65%,transparent)]" />
        <p className="gaia-kicker">{eyebrow}</p>
      </div>
      <h1 className="gaia-display mt-5 max-w-[18ch]">{title}</h1>
      <p className="text-muted-foreground mt-6 max-w-3xl text-lg leading-8 text-pretty sm:text-xl">
        {description}
      </p>
    </header>
  )
}
