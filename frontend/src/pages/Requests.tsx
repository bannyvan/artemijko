import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../api/client'
import { useForm } from 'react-hook-form'

export function Requests() {
  const qc = useQueryClient()
  const { data: items } = useQuery({ queryKey: ['requests'], queryFn: async () => (await api.get('/requests')).data })
  const { register, handleSubmit, reset } = useForm({ defaultValues: { type: 'dayoff', days: 1, from_date: '', to_date: '', comment: '' } })
  const create = useMutation({ mutationFn: async (payload: any) => (await api.post('/requests', payload)).data, onSuccess: () => { qc.invalidateQueries({ queryKey: ['requests'] }); reset() } })

  return (
    <div className="bg-white p-4 rounded shadow">
      <h2 className="font-semibold mb-2">Заявки</h2>
      <form className="space-y-2" onSubmit={handleSubmit((d) => create.mutate(d))}>
        <select className="border p-2 rounded w-full" {...register('type')}>
          <option value="vacation">Отпуск</option>
          <option value="dayoff">Отгул</option>
          <option value="sick">Больничный</option>
        </select>
        <input className="border p-2 rounded w-full" placeholder="С даты" type="date" {...register('from_date')} />
        <input className="border p-2 rounded w-full" placeholder="По дату" type="date" {...register('to_date')} />
        <input className="border p-2 rounded w-full" placeholder="Дней" type="number" {...register('days', { valueAsNumber: true })} />
        <input className="border p-2 rounded w-full" placeholder="Комментарий" {...register('comment')} />
        <button className="w-full bg-blue-600 text-white py-2 rounded" type="submit">Создать</button>
      </form>
      <ul className="mt-3 text-sm space-y-1">
        {(items||[]).map((r:any) => <li key={r.id}>#{r.id} {r.type} {r.status}</li>)}
      </ul>
    </div>
  )
}