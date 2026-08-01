import type { NextRequest } from 'next/server'
import { NextResponse } from 'next/server'

// Gate operational routes behind HTTP Basic auth.
// REVIEW_BASIC_AUTH holds "user:password". Unset denies all access (secure default).
export function middleware(request: NextRequest) {
  const expected = process.env.REVIEW_BASIC_AUTH
  if (!expected) {
    return new NextResponse('Administrative access is not configured.', {
      status: 503,
    })
  }

  const header = request.headers.get('authorization') ?? ''
  const [scheme, encoded] = header.split(' ')
  let provided = ''
  if (scheme === 'Basic' && encoded) {
    try {
      provided = atob(encoded)
    } catch {
      provided = ''
    }
  }

  if (provided !== expected) {
    return new NextResponse('Authentication required.', {
      status: 401,
      headers: {
        'WWW-Authenticate': 'Basic realm="GaiaFAAC Administration"',
      },
    })
  }

  return NextResponse.next()
}

export const config = { matcher: ['/review/:path*', '/admin/:path*'] }
