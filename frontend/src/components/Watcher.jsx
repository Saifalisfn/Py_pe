import { useEffect, useState } from 'react'
import { getWatcherStatus, startWatcher, stopWatcher, getConfig, updateConfig } from '../api'
import { Play, Square, Settings, Loader2 } from 'lucide-react'

export default function Watcher() {
  const [running, setRunning] = useState(false)
  const [loading, setLoading] = useState(false)
  const [config, setConfig] = useState(null)
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({})
  const [saving, setSaving] = useState(false)

  const loadStatus = () =>
    getWatcherStatus().then(r => setRunning(r.data.running)).catch(() => {})

  const loadConfig = () =>
    getConfig().then(r => { setConfig(r.data); setForm(r.data) }).catch(() => {})

  useEffect(() => { loadStatus(); loadConfig() }, [])

  useEffect(() => {
    if (!running) return
    const id = setInterval(loadStatus, 10000)
    return () => clearInterval(id)
  }, [running])

  const toggle = async () => {
    setLoading(true)
    try {
      running ? await stopWatcher() : await startWatcher()
      await loadStatus()
    } finally { setLoading(false) }
  }

  const save = async () => {
    setSaving(true)
    const updates = {}
    if (form.polling_interval) updates.polling_interval = parseInt(form.polling_interval)
    if (form.webhook_url !== config.webhook_url) updates.webhook_url = form.webhook_url
    if (form.webhook_enabled !== config.webhook_enabled) updates.webhook_enabled = form.webhook_enabled === 'true'
    if (form.telegram_enabled !== config.telegram_enabled) updates.telegram_enabled = form.telegram_enabled === 'true'
    try { await updateConfig(updates); await loadConfig(); setEditing(false) }
    catch (e) { alert(e.response?.data?.detail || 'Save failed') }
    finally { setSaving(false) }
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">Background Watcher</h2>
        <button
          onClick={toggle}
          disabled={loading}
          className={`flex items-center gap-2 text-sm px-4 py-2 rounded-lg font-medium ${
            running
              ? 'bg-red-500/20 hover:bg-red-500/30 text-red-400'
              : 'bg-green-500/20 hover:bg-green-500/30 text-green-400'
          } disabled:opacity-50`}
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : running ? <Square size={14} /> : <Play size={14} />}
          {running ? 'Stop' : 'Start'}
        </button>
      </div>

      <div className="flex items-center gap-2 mb-4">
        <div className={`w-2 h-2 rounded-full ${running ? 'bg-green-400 animate-pulse' : 'bg-gray-600'}`} />
        <span className={`text-sm ${running ? 'text-green-400' : 'text-gray-500'}`}>
          {running ? 'Running' : 'Stopped'}
        </span>
        {config?.polling_interval && (
          <span className="text-gray-600 text-xs ml-1">· polls every {config.polling_interval}s</span>
        )}
      </div>

      {config && (
        <div>
          <button
            onClick={() => setEditing(!editing)}
            className="flex items-center gap-1.5 text-gray-500 hover:text-gray-300 text-xs mb-3"
          >
            <Settings size={12} /> {editing ? 'Cancel' : 'Configure'}
          </button>

          {editing && (
            <div className="space-y-3 border-t border-gray-800 pt-3">
              <div>
                <label className="text-gray-400 text-xs block mb-1">Polling interval (seconds)</label>
                <input
                  type="number"
                  value={form.polling_interval || ''}
                  onChange={e => setForm(f => ({ ...f, polling_interval: e.target.value }))}
                  className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-white text-sm w-32 focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="text-gray-400 text-xs block mb-1">Webhook URL</label>
                <input
                  value={form.webhook_url || ''}
                  onChange={e => setForm(f => ({ ...f, webhook_url: e.target.value }))}
                  className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-white text-sm w-full focus:outline-none focus:border-blue-500"
                  placeholder="https://..."
                />
              </div>
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.webhook_enabled === 'true' || form.webhook_enabled === true}
                    onChange={e => setForm(f => ({ ...f, webhook_enabled: String(e.target.checked) }))}
                    className="accent-blue-500"
                  />
                  Webhook enabled
                </label>
                <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.telegram_enabled === 'true' || form.telegram_enabled === true}
                    onChange={e => setForm(f => ({ ...f, telegram_enabled: String(e.target.checked) }))}
                    className="accent-blue-500"
                  />
                  Telegram enabled
                </label>
              </div>
              <button
                onClick={save}
                disabled={saving}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg flex items-center gap-2"
              >
                {saving && <Loader2 size={12} className="animate-spin" />} Save
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
