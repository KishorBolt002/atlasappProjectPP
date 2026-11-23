import { BrowserRouter, NavLink, Route, Routes, useLocation } from 'react-router'
import { Toaster } from 'sonner'
import { FileText } from 'lucide-react'
import { useMe, type Me } from '@/hooks/useMe'
import NotesPage from '@/pages/NotesPage'
import CatalogPage from '@/pages/CatalogPage'
import ProductPage from '@/pages/ProductPage'
import AttributesPage from '@/pages/AttributesPage'
import CoveragePage from '@/pages/CoveragePage'
import UsersPage from '@/pages/UsersPage'
import { AdminOnly } from '@/components/catalog/AdminOnly'

const navCls = ({ isActive }: { isActive: boolean }) =>
  `rounded-lg px-3 py-2 text-sm font-semibold whitespace-nowrap transition-colors focus-visible:outline-2 focus-visible:outline-cobalt ${
    isActive ? 'bg-cobalt text-white' : 'text-ink-soft hover:bg-cobalt-wash hover:text-ink'
  }`

function Header({ me }: { me: Me | null }) {
  const { pathname } = useLocation()
  const inBrowse = pathname === '/catalog' || pathname.startsWith('/catalog/products/')
  return (
    <header className="border-b border-line bg-sheet">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-3 px-5 py-3 sm:px-8">
        <NavLink to="/" className="flex items-center gap-3">
          <span className="grid size-9 place-items-center rounded-lg bg-cobalt text-white">
            <FileText className="size-5" />
          </span>
          <span className="text-xl font-extrabold tracking-tight">Sync Test Notes</span>
        </NavLink>
        <nav aria-label="Main" className="-mx-1 flex flex-1 gap-1 overflow-x-auto px-1">
          <NavLink to="/" end className={navCls}>
            Notes
          </NavLink>
          {me?.is_admin && (
            <>
              <NavLink to="/catalog" className={() => navCls({ isActive: inBrowse })}>
                Product catalog
              </NavLink>
              <NavLink to="/catalog/attributes" className={navCls}>
                Attributes
              </NavLink>
              <NavLink to="/catalog/coverage" className={navCls}>
                Coverage and sync
              </NavLink>
              <NavLink to="/users" className={navCls}>
                Users
              </NavLink>
            </>
          )}
        </nav>
        {me && (
          <span className="text-sm text-ink-soft">
            {me.name || me.email}
            <span className="ml-2 rounded-full bg-cobalt-wash px-2 py-0.5 text-xs font-semibold text-cobalt-deep">
              {me.role}
            </span>
          </span>
        )}
      </div>
    </header>
  )
}

export default function App() {
  const { me, loaded } = useMe()
  const guard = (el: React.ReactNode) => (
    <AdminOnly me={me} loaded={loaded}>
      {el}
    </AdminOnly>
  )
  return (
    <BrowserRouter>
      <div className="min-h-screen">
        <Toaster position="bottom-right" richColors closeButton />
        <Header me={me} />
        <Routes>
          <Route path="/" element={<NotesPage />} />
          <Route path="/catalog" element={guard(<CatalogPage />)} />
          <Route path="/catalog/products/:productId" element={guard(<ProductPage />)} />
          <Route path="/catalog/attributes" element={guard(<AttributesPage />)} />
          <Route path="/catalog/coverage" element={guard(<CoveragePage />)} />
          <Route path="/users" element={guard(<UsersPage />)} />
          <Route
            path="*"
            element={
              <main className="mx-auto max-w-3xl px-5 py-16 text-center">
                <p className="text-lg font-bold">This page doesn’t exist.</p>
                <NavLink to="/" className="mt-3 inline-block font-semibold text-cobalt">
                  Go to notes
                </NavLink>
              </main>
            }
          />
        </Routes>
      </div>
    </BrowserRouter>
  )
}
