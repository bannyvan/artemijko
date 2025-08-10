import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../api/client'
import { useMainButton } from '../hooks/useMainButton'
import { useState } from 'react'

const ruStatus = (s: string) => s === 'active' ? 'активна' : s === 'paused' ? 'пауза' : 'завершена'

export function TimeTracker() {
  const qc = useQueryClient()
  const [note, setNote] = useState('')

  const { data: me } = useQuery({ queryKey: ['me'], queryFn: async () => (await api.get('/me')).data })
  const { data: shifts } = useQuery({ queryKey: ['shifts'], queryFn: async () => (await api.get('/shifts')).data })
  const active = shifts?.find((s: any) => s.status !== 'finished')

  const start = useMutation({ mutationFn: async () => (await api.post('/shifts/start', { note })).data, onSuccess: () => qc.invalidateQueries({ queryKey: ['shifts'] }) })
  const pause = useMutation({ mutationFn: async () => (await api.post('/shifts/pause')).data, onSuccess: () => qc.invalidateQueries({ queryKey: ['shifts'] }) })
  const resume = useMutation({ mutationFn: async () => (await api.post('/shifts/resume')).data, onSuccess: () => qc.invalidateQueries({ queryKey: ['shifts'] }) })
  const finish = useMutation({ mutationFn: async () => (await api.post('/shifts/finish')).data, onSuccess: () => qc.invalidateQueries({ queryKey: ['shifts'] }) })

  useMainButton({
    text: active ? (active.status === 'active' ? 'Пауза' : 'Продолжить') : 'Старт',
    onClick: () => {
      if (!active) start.mutate()
      else if (active.status === 'active') pause.mutate()
      else resume.mutate()
    },
    visible: true
  })

  return (
    <div className="bg-white p-4 rounded shadow">
      <h2 className="font-semibold mb-2">Трекер</h2>
      <div className="space-y-2">
        {!active && (
          <input className="border rounded p-2 w-full" placeholder="Заметка" value={note} onChange={(e) => setNote(e.target.value)} />
        )}
        {active && (
          <div className="text-sm text-gray-600">Статус: {ruStatus(active.status)}</div>
        )}
        {active && (
          <button className="w-full bg-red-500 text-white py-2 rounded" onClick={() => finish.mutate()}>Завершить смену</button>
        )}
      </div>
    </div>
  )
}