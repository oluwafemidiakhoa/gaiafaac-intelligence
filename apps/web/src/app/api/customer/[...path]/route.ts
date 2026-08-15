import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'

const SESSION_COOKIE = 'gaiafaac_session'

function apiBaseUrl() {
  return (
    process.env.API_INTERNAL_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    'http://localhost:8000'
  ).replace(/\/$/, '')
}

async function proxy(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params
  const relativePath = path.join('/')
  const incomingUrl = new URL(request.url)
  const target = new URL(`${apiBaseUrl()}/api/v1/${relativePath}`)
  target.search = incomingUrl.search

  const jar = await cookies()
  const token = jar.get(SESSION_COOKIE)?.value
  const headers = new Headers()
  const contentType = request.headers.get('content-type')
  if (contentType) headers.set('Content-Type', contentType)
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const method = request.method
  const body =
    method === 'GET' || method === 'HEAD'
      ? undefined
      : await request.arrayBuffer()
  const response = await fetch(target, {
    method,
    headers,
    body,
    cache: 'no-store',
  })

  const isSessionResponse =
    relativePath === 'account/login' ||
    relativePath === 'account/register' ||
    relativePath === 'account/team/accept-invite'

  if (isSessionResponse && response.ok) {
    const payload = (await response.json()) as {
      token: string
      expires_at: string
    }
    const outgoing = NextResponse.json({
      ok: true,
      expires_at: payload.expires_at,
    })
    outgoing.cookies.set(SESSION_COOKIE, payload.token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      expires: new Date(payload.expires_at),
    })
    return outgoing
  }

  if (relativePath === 'account/logout') {
    const outgoing = new NextResponse(null, {
      status: response.ok ? 204 : response.status,
    })
    outgoing.cookies.set(SESSION_COOKIE, '', {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      maxAge: 0,
    })
    return outgoing
  }

  const responseHeaders = new Headers()
  const outgoingContentType = response.headers.get('content-type')
  const disposition = response.headers.get('content-disposition')
  if (outgoingContentType)
    responseHeaders.set('Content-Type', outgoingContentType)
  if (disposition) responseHeaders.set('Content-Disposition', disposition)
  return new NextResponse(await response.arrayBuffer(), {
    status: response.status,
    headers: responseHeaders,
  })
}

export const GET = proxy
export const POST = proxy
export const DELETE = proxy
