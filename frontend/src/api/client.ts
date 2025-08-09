import axios from 'axios'

const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || '/api' })

let accessToken: string | null = null
export function setAccessToken(token: string | null) { accessToken = token }

api.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`
  const url = config.url || ''
  if (config.method === 'post' && (/\/shifts\/(start|finish)/.test(url))) {
    if (!config.headers['Idempotency-Key']) {
      const key = `${Date.now()}-${Math.random().toString(36).slice(2)}`
      config.headers['Idempotency-Key'] = key
    }
  }
  return config
})

api.interceptors.response.use(undefined, async (error) => {
  const { response, config } = error
  if (response?.status === 401 && !config.__retry) {
    config.__retry = true
    try {
      const r = await api.post('/auth/refresh', undefined, { withCredentials: true })
      setAccessToken(r.data.access_token)
      config.headers.Authorization = `Bearer ${r.data.access_token}`
      return api.request(config)
    } catch (e) {
      // fallthrough
    }
  }
  return Promise.reject(error)
})

export default api