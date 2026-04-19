import { useEffect, useState } from 'react'
import { getTransactions, getSessions, fetchTransactions } from '../api'
import { RefreshCw, Loader2 } from 'lucide-react'

const STATUS_COLOR = {
  SUCCESS: 'bg-green-500/20 text-green-400',
  FAILED: 'bg-red-500/20 text-red-400',
  PENDING: 'bg-yellow-500/20 text-yellow-400',
}

export default function Transactions({ refresh }) {
  const [txns, setTxns] = useState([])
  const [sessions, setSessions] = useState([])
  const [mobile, setMobile] = useState('')
  const [loading, setLoading] = useState(false)
  const [fetching, setFetching] = useState(false)

  useEffect(() => {
    getSessions().then(r => setSessions(r.data.sessions)).catch(() => {})
  }, [refresh])

  const load = (m) => {
    setLoading(true)
    getTransactions(m || undefined, 100)
      .then(r => setTxns(r.data.transactions))
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => { load(mobile) }, [refresh])

  const handleMobileChange = (m) => { setMobile(m); load(m) }

  const triggerFetch = async () => {
    setFetching(true)
    try { await fetchTransactions(mobile || undefined); load(mobile) }
    catch (e) { alert(e.response?.data?.detail || 'Fetch failed') }
    finally { setFetching(false) }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
        <h2 className="text-lg font-semibold text-white">Transactions</h2>
        <div className="flex gap-2 items-center">
          <select
            value={mobile}
            onChange={e => handleMobileChange(e.target.value)}
            className="bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-blue-500"
          >
            <option value="">All accounts</option>
            {sessions.map(s => <option key={s.mobile} value={s.mobile}>{s.mobile}</option>)}
          </select>
          <button
            onClick={triggerFetch}
            disabled={fetching}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm px-3 py-1.5 rounded-lg flex items-center gap-1.5"
          >
            {fetching ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
            Fetch Live
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-10"><Loader2 size={24} className="animate-spin text-gray-600" /></div>
      ) : txns.length === 0 ? (
        <p className="text-gray-500 text-sm">No transactions. Click "Fetch Live" to pull from BharatPe.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-500 border-b border-gray-800 text-left">
                <th className="pb-3 pr-4 font-medium">Date</th>
                <th className="pb-3 pr-4 font-medium">Account</th>
                <th className="pb-3 pr-4 font-medium">Amount</th>
                <th className="pb-3 pr-4 font-medium">Payer</th>
                <th className="pb-3 pr-4 font-medium">UTR</th>
                <th className="pb-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {txns.map((t, i) => (
                <tr key={i} className="border-b border-gray-800/50 hover:bg-gray-900/50">
                  <td className="py-3 pr-4 text-gray-400 whitespace-nowrap">
                    {t.transaction_date ? String(t.transaction_date).slice(0, 16) : '—'}
                  </td>
                  <td className="py-3 pr-4 text-gray-300">{t.session_mobile}</td>
                  <td className="py-3 pr-4 text-green-400 font-medium">₹{t.amount}</td>
                  <td className="py-3 pr-4 text-gray-300 max-w-32 truncate">{t.payer_name || '—'}</td>
                  <td className="py-3 pr-4 font-mono text-gray-400 text-xs">{t.utr || '—'}</td>
                  <td className="py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_COLOR[t.status] || 'bg-gray-700 text-gray-400'}`}>
                      {t.status || 'UNKNOWN'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
