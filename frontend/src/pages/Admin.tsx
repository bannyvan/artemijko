import { useQuery } from '@tanstack/react-query'
import api from '../api/client'

const ruRole = (r: string) => r==='admin' ? 'админ' : r==='manager' ? 'менеджер' : 'сотрудник'

export function Admin() {
  const { data: users } = useQuery({ queryKey: ['admin','users'], queryFn: async () => (await api.get('/admin/users')).data, retry: 0 })
  return (
    <div className="bg-white p-4 rounded shadow">
      <h2 className="font-semibold mb-2">Админка</h2>
      <div className="mb-2 text-sm text-gray-700">Пользователи</div>
      <ul className="text-sm space-y-1">
        {(users||[]).map((u:any) => <li key={u.id}>#{u.id} {u.tg_id} — {ruRole(u.role)}</li>)}
      </ul>
    </div>
  )
}