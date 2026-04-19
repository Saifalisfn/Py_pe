import { useEffect, useState } from 'react'
import { getSessions, deleteSession, fetchTransactions } from '../api'
import { Trash2, RefreshCw, Loader2, User } from 'lucide-react'

export default function Sessions({ refresh, onRefresh }) {
  const [sessions, setSessions] = useState([])
  const [loadingMap, setLoadingMap] = useState({})

  const load = () => getSessions().then(r => setSessions(r.data.sessions)).catch(() => {})

  useEffect(() => { load() }, [refresh])

  const remove = async (mobile) => {
    if (!confirm(`Remove session for ${mobile}?`)) return
    await deleteSession(mobile)
    load()
    onRefresh?.()
  }

  const fetch = async (mobile) => {
    setLoadingMap(m => ({ ...m, [mobile]: 'fetch' }))
    try {
      await fetchTransactions(mobile)
      onRefresh?.()
    } catch (e) {
      alert(e.response?.data?.detail || 'Fetch failed')
    } finally {
      setLoadingMap(m => ({ ...m, [mobile]: null }))
    }
  }

  if (!sessions.length)
    return <p className="text-gray-500 text-sm">No active sessions. Add a merchant account above.</p>

  return (
    <div>
      <h2 className="text-lg font-semibold text-white mb-4">Active Sessions ({sessions.length})</h2>
      <div className="space-y-2">
        {sessions.map(s => (
          <div key={s.mobile} className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-blue-500/20 text-blue-400 p-2 rounded-lg">
                <User size={16} />
              </div>
              <div>
                <p className="text-white font-medium text-sm">{s.mobile}</p>
                <p className="text-gray-500 text-xs">MID: {s.merchant_id} · {s.updated_at?.slice(0, 16)}</p>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => fetch(s.mobile)}
                disabled={!!loadingMap[s.mobile]}
                className="bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-gray-300 text-xs px-3 py-1.5 rounded-lg flex items-center gap-1.5"
              >
                {loadingMap[s.mobile] === 'fetch'
                  ? <Loader2 size={12} className="animate-spin" />
                  : <RefreshCw size={12} />}
                Fetch
              </button>
              <button
                onClick={() => remove(s.mobile)}
                className="bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs px-3 py-1.5 rounded-lg flex items-center gap-1.5"
              >
                <Trash2 size={12} /> Remove
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
