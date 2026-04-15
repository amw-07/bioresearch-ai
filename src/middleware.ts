import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const PUBLIC_ROUTES = new Set([
  '/',
  '/login',
  '/register',
  '/reset-password',
  '/verify-email',
  '/dashboard',
  '/dashboard/search',
  '/dashboard/scoring',
])

const AUTH_REQUIRED_PREFIXES = [
  '/dashboard/researchers',
  '/settings',
]

export function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token')?.value
  const { pathname } = request.nextUrl

  const isPublic = PUBLIC_ROUTES.has(pathname) ||
    AUTH_REQUIRED_PREFIXES.every(prefix => !pathname.startsWith(prefix))

  if (!isPublic && !token) {
    const url = new URL('/login', request.url)
    url.searchParams.set('from', pathname)
    return NextResponse.redirect(url)
  }

  if (token && (pathname === '/login' || pathname === '/register')) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
}
