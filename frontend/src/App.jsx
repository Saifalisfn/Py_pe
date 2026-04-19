import { useState } from 'react'
import Stats from './components/Stats'
import Login from './components/Login'
import Sessions from './components/Sessions'
import Transactions from './components/Transactions'
import UTRSearch from './components/UTRSearch'
import Watcher from './components/Watcher'
import { LayoutDashboard, CreditCard, Search, BookOpen } from 'lucide-react'

const TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'transactions', label: 'Transactions', icon: CreditCard },
  { id: 'utr', label: 'UTR Search', icon: Search },
  { id: 'docs', label: 'API Docs', icon: BookOpen, href: '/api/docs' },
]

export default function App() {
  const [tab, setTab] = useState('dashboard')
  const [refresh, setRefresh] = useState(0)
  const bump = () => setRefresh(r => r + 1)

  return (
    <div className="min-h-screen bg-[#0f1117] text-gray-100 flex flex-col">
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 text-white text-xs font-bold px-2 py-1 rounded">BP</div>
          <span className="font-semibold text-white">BharatPe Manager</span>
        </div>
        <nav className="flex gap-1">
          {TABS.map(t =>
            t.href ? (
              <a
                key={t.id}
                href={t.href}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
              >
                <t.icon size={15} />
                <span className="hidden sm:inline">{t.label}</span>
              </a>
            ) : (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                  tab === t.id
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}
              >
                <t.icon size={15} />
                <span className="hidden sm:inline">{t.label}</span>
              </button>
            )
          )}
        </nav>
      </header>

      <main className="flex-1 px-6 py-6 max-w-6xl mx-auto w-full">
        {tab === 'dashboard' && (
          <div className="space-y-6">
            <Stats refresh={refresh} />
            <div className="grid lg:grid-cols-2 gap-6">
              <div className="space-y-6">
                <Login onSuccess={bump} />
                <Sessions refresh={refresh} onRefresh={bump} />
              </div>
              <Watcher />
            </div>
          </div>
        )}

        {tab === 'transactions' && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <Transactions refresh={refresh} />
          </div>
        )}

        {tab === 'utr' && (
          <div className="max-w-xl">
            <UTRSearch />
          </div>
        )}
      </main>
    </div>
  )
}
