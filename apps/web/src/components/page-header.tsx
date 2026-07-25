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
    <header className="max-w-3xl">
      <p className="text-primary font-mono text-xs font-semibold tracking-[0.18em] uppercase">
        {eyebrow}
      </p>
      <h1 className="mt-4 text-4xl font-semibold tracking-[-0.035em] text-balance sm:text-5xl">
        {title}
      </h1>
      <p className="text-muted-foreground mt-5 text-lg leading-8 text-pretty">
        {description}
      </p>
    </header>
  )
}
