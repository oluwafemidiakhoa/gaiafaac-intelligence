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
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-muted-foreground text-sm font-medium">
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="font-mono text-2xl font-semibold tracking-tight">
          {value}
        </p>
        <p className="text-muted-foreground mt-2 text-xs leading-5">{detail}</p>
      </CardContent>
    </Card>
  )
}
