import { useQuery } from '@tanstack/react-query'
import api from '../api/client'

const ruStatus = (s: string) => s === 'active' ? 'активна' : s === 'paused' ? 'пауза' : 'завершена'

export function MyDay() {
  const { data: shifts } = useQuery({ queryKey: ['shifts'], queryFn: async () => (await api.get('/shifts')).data })
  return (
    <div className="bg-white p-4 rounded shadow">
      <h2 className="font-semibold mb-2">Мой день</h2>
      <ul className="space-y-1 text-sm">
        {(shifts || []).slice(0, 5).map((s: any) => (
          <li key={s.id} className="flex justify-between">
            <span>Смена #{s.id}</span>
            <span>{ruStatus(s.status)}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}