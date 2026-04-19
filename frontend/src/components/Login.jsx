import { useState } from 'react'
import { requestOtp, verifyOtp } from '../api'
import { Phone, KeyRound, Loader2 } from 'lucide-react'

export default function Login({ onSuccess }) {
  const [mobile, setMobile] = useState('')
  const [otp, setOtp] = useState('')
  const [step, setStep] = useState('mobile') // 'mobile' | 'otp'
  const [loading, setLoading] = useState(false)
  const [msg, setMsg] = useState(null)
  const [error, setError] = useState(null)

  const sendOtp = async () => {
    if (!mobile.trim()) return
    setLoading(true); setError(null); setMsg(null)
    try {
      const r = await requestOtp(mobile.trim())
      setMsg(r.data.message)
      setStep('otp')
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to send OTP')
    } finally {
      setLoading(false)
    }
  }

  const verify = async () => {
    if (!otp.trim()) return
    setLoading(true); setError(null)
    try {
      const r = await verifyOtp(mobile.trim(), otp.trim())
      setMsg(r.data.message)
      onSuccess?.()
      setStep('mobile'); setMobile(''); setOtp('')
    } catch (e) {
      setError(e.response?.data?.detail || 'Verification failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 max-w-sm">
      <h2 className="text-lg font-semibold text-white mb-4">Add Merchant Account</h2>

      {msg && <p className="text-green-400 text-sm mb-3">{msg}</p>}
      {error && <p className="text-red-400 text-sm mb-3">{error}</p>}

      {step === 'mobile' ? (
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Phone size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-9 pr-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
              placeholder="Mobile number"
              value={mobile}
              onChange={e => setMobile(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendOtp()}
            />
          </div>
          <button
            onClick={sendOtp}
            disabled={loading || !mobile.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm px-4 py-2 rounded-lg flex items-center gap-2"
          >
            {loading ? <Loader2 size={14} className="animate-spin" /> : 'Send OTP'}
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          <p className="text-gray-400 text-sm">OTP sent to <span className="text-white">{mobile}</span></p>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <KeyRound size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
              <input
                className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-9 pr-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                placeholder="Enter OTP"
                value={otp}
                onChange={e => setOtp(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && verify()}
                autoFocus
              />
            </div>
            <button
              onClick={verify}
              disabled={loading || !otp.trim()}
              className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm px-4 py-2 rounded-lg flex items-center gap-2"
            >
              {loading ? <Loader2 size={14} className="animate-spin" /> : 'Verify'}
            </button>
          </div>
          <button onClick={() => setStep('mobile')} className="text-gray-500 text-xs hover:text-gray-300">
            ← Back
          </button>
        </div>
      )}
    </div>
  )
}
