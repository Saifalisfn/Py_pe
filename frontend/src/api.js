import axios from 'axios'

const client = axios.create({ baseURL: '/api' })

export const requestOtp = (mobile) => client.post('/auth/request-otp', { mobile })
export const verifyOtp = (mobile, otp) => client.post('/auth/verify-otp', { mobile, otp })

export const getSessions = () => client.get('/sessions')
export const deleteSession = (mobile) => client.delete(`/sessions/${mobile}`)

export const getTransactions = (mobile, limit = 50) =>
  client.get('/transactions', { params: { mobile, limit } })
export const fetchTransactions = (mobile) =>
  client.post('/transactions/fetch', null, { params: mobile ? { mobile } : {} })

export const searchUtr = (utr) => client.get(`/utr/${encodeURIComponent(utr)}`)

export const getStats = () => client.get('/stats')

export const getConfig = () => client.get('/config')
export const updateConfig = (data) => client.put('/config', data)

export const getWatcherStatus = () => client.get('/watcher/status')
export const startWatcher = () => client.post('/watcher/start')
export const stopWatcher = () => client.post('/watcher/stop')
