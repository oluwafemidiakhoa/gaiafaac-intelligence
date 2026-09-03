import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function MetricCard({
  label,
  value,
  detail,
}: {
  label: string
  value: string
  detail: string
}) {
  return (
    <Card className="group relative overflow-hidden">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/40 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
      <CardHeader className="pb-3">
        <CardTitle className="gaia-data-label">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="gaia-data-value text-foreground">{value}</p>
        <p className="text-muted-foreground mt-3 text-xs leading-5">{detail}</p>
      </CardContent>
    </Card>
  )
}
