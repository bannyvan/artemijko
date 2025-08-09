import { useEffect } from 'react'
import api, { setAccessToken } from '../api/client'

export function Profile() {
  const login = async () => {
    const urlParams = new URLSearchParams(window.location.search)
    const initData = urlParams.get('tgWebAppData') || urlParams.get('initData')
    if (initData) {
      const r = await api.post('/auth/telegram', null, { params: { initData }, withCredentials: true })
      setAccessToken(r.data.access_token)
    }
  }

  useEffect(() => { login() }, [])

  return (
    <div className="bg-white p-4 rounded shadow">
      <h2 className="font-semibold mb-2">Профиль</h2>
      <p className="text-sm text-gray-600">Авторизация через Telegram WebApp initData</p>
    </div>
  )
}