import { useEffect } from 'react'
import { useTelegram } from './useTelegram'

export function useMainButton({ text, onClick, visible = true }: { text: string, onClick: () => void, visible?: boolean }) {
  const { MainButton } = useTelegram()

  useEffect(() => {
    if (!MainButton) return
    MainButton.setText(text)
    if (visible) MainButton.show(); else MainButton.hide()
    const handler = onClick
    MainButton.onClick(handler)
    return () => MainButton.offClick(handler)
  }, [MainButton, text, onClick, visible])
}