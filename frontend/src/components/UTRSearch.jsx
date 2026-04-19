import { useState } from 'react'
import { searchUtr } from '../api'
import { Search, Loader2, CheckCircle, XCircle } from 'lucide-react'

export default function UTRSearch() {
  const [utr, setUtr] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  const search = async () => {
    if (!utr.trim()) return
    setLoading(true); setSearched(false); setResult(null)
    try {
      const r = await searchUtr(utr.trim())
      setResult(r.data)
    } catch (e) {
      setResult({ found: false, error: e.response?.data?.detail || 'Search error' })
    } finally {
      setLoading(false); setSearched(true)
    }
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <h2 className="text-lg font-semibold text-white mb-4">UTR Search</h2>

      <div className="flex gap-2 mb-4">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-9 pr-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500 font-mono"
            placeholder="Enter UTR number"
            value={utr}
            onChange={e => setUtr(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && search()}
          />
        </div>
        <button
          onClick={search}
          disabled={loading || !utr.trim()}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm px-4 py-2 rounded-lg flex items-center gap-2"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : 'Search'}
        </button>
      </div>

      {searched && result && (
        <div className={`rounded-lg p-4 border ${result.found ? 'border-green-500/30 bg-green-500/5' : 'border-red-500/30 bg-red-500/5'}`}>
          <div className="flex items-center gap-2 mb-2">
            {result.found
              ? <CheckCircle size={16} className="text-green-400" />
              : <XCircle size={16} className="text-red-400" />}
            <span className={`font-medium text-sm ${result.found ? 'text-green-400' : 'text-red-400'}`}>
              {result.found ? 'Transaction found' : 'Not found in any account'}
            </span>
          </div>
          {result.found && result.data && (
            <div className="space-y-1 text-sm">
              {[
                ['Amount', `₹${result.data.amount}`],
                ['Status', result.data.status],
                ['Payer', result.data.payer_name || result.data.payerName],
                ['Payer VPA', result.data.payer_vpa || result.data.payerVpa],
                ['Account', result.data.session_mobile],
                ['Date', result.data.transaction_date],
              ].filter(([, v]) => v).map(([k, v]) => (
                <div key={k} className="flex gap-2">
                  <span className="text-gray-500 w-24 shrink-0">{k}</span>
                  <span className="text-gray-200">{String(v)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
