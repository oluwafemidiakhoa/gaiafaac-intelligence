import { CircleAlert } from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function DataUnavailable({ message }: { message: string }) {
  return (
    <Card className="border-dashed">
      <CardHeader>
        <CircleAlert
          className="text-muted-foreground size-5"
          aria-hidden="true"
        />
        <CardTitle className="pt-2 text-lg">Demo data unavailable</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground max-w-2xl text-sm leading-6">
          {message} No figures have been substituted or inferred.
        </p>
      </CardContent>
    </Card>
  )
}
