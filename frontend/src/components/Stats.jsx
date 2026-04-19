import { useEffect, useState } from 'react'
import { getStats } from '../api'
import { Activity, CreditCard, Bell, Search } from 'lucide-react'

const Card = ({ icon: Icon, label, value, color }) => (
  <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex items-center gap-4">
    <div className={`p-3 rounded-lg ${color}`}>
      <Icon size={20} />
    </div>
    <div>
      <p className="text-gray-400 text-sm">{label}</p>
      <p className="text-2xl font-semibold text-white">{value ?? '—'}</p>
    </div>
  </div>
)

export default function Stats({ refresh }) {
  const [data, setData] = useState(null)

  useEffect(() => {
    getStats().then(r => setData(r.data)).catch(() => {})
  }, [refresh])

  return (
    <div>
      <h2 className="text-lg font-semibold text-white mb-4">Overview</h2>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card icon={Activity} label="Active Sessions" value={data?.active_sessions} color="bg-blue-500/20 text-blue-400" />
        <Card icon={CreditCard} label="Transactions" value={data?.total_transactions} color="bg-green-500/20 text-green-400" />
        <Card icon={Bell} label="Notifications" value={data?.total_notifications} color="bg-yellow-500/20 text-yellow-400" />
        <Card icon={Search} label="UTR Searches" value={data?.utr_searches} color="bg-purple-500/20 text-purple-400" />
      </div>

      {data?.recent_utr_searches?.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-sm font-medium text-gray-400 mb-3">Recent UTR Searches</h3>
          <div className="space-y-2">
            {data.recent_utr_searches.map((s, i) => (
              <div key={i} className="flex items-center justify-between text-sm">
                <span className="font-mono text-gray-300">{s.utr}</span>
                <div className="flex items-center gap-3">
                  <span className="text-gray-500 text-xs">{s.searched_at}</span>
                  <span className={s.found ? 'text-green-400' : 'text-red-400'}>
                    {s.found ? '✓ Found' : '✗ Not Found'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
