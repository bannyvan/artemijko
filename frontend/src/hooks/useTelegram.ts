import { useEffect, useState } from 'react'

declare global {
  interface Window { Telegram: any }
}

export function useTelegram() {
  const [ready, setReady] = useState(false)
  const tg = (window as any).Telegram?.WebApp

  useEffect(() => {
    if (tg) {
      tg.ready()
      setReady(true)
    }
  }, [tg])

  const expand = () => tg?.expand?.()
  const MainButton = tg?.MainButton
  const BackButton = tg?.BackButton
  const themeParams = tg?.themeParams || {}
  const haptic = tg?.HapticFeedback

  return { tg, ready, expand, MainButton, BackButton, themeParams, haptic }
}