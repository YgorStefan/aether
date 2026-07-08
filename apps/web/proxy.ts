import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

const APP_ROUTES = ['/dashboard', '/run', '/history', '/settings', '/admin']
const AUTH_ROUTES = new Set(['/login', '/signup'])

export function isAppRoute(path: string): boolean {
  return APP_ROUTES.some((r) => path.startsWith(r))
}

export function isAuthRoute(path: string): boolean {
  return AUTH_ROUTES.has(path)
}

export async function proxy(request: NextRequest) {
  let response = NextResponse.next({ request })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
          response = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) =>
            response.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  const { data: { user } } = await supabase.auth.getUser()

  const path = request.nextUrl.pathname

  if (!user && isAppRoute(path)) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  if (user && isAuthRoute(path)) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  return response
}

// O Next.js analisa este matcher estaticamente, sem executar o arquivo, e não reconhece
// TaggedTemplateExpression (String.raw quebra o build com "Unsupported node type") — por
// isso precisa ser um literal de string simples, com as barras escapadas manualmente.
export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon\\.ico|.*\\.(?:svg|png|jpg|gif|webp)$).*)'], // NOSONAR
}
