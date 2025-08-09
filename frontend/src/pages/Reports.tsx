import api from '../api/client'
import { useState } from 'react'

export function Reports() {
  const [period, setPeriod] = useState<'day'|'week'|'month'>('day')

  const download = async (type: 'csv' | 'xlsx') => {
    const url = `/reports/export.${type}?period=${period}`
    const r = await api.get(url, { responseType: 'blob' })
    const blob = new Blob([r.data])
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `report.${type}`
    a.click()
  }

  return (
    <div className="bg-white p-4 rounded shadow">
      <h2 className="font-semibold mb-2">Отчёты</h2>
      <div className="flex gap-2 mb-2">
        {(['day','week','month'] as const).map(p => (
          <button key={p} className={`px-3 py-1 rounded ${period===p?'bg-blue-600 text-white':'bg-gray-200'}`} onClick={() => setPeriod(p)}>{p}</button>
        ))}
      </div>
      <div className="flex gap-2">
        <button className="bg-gray-700 text-white px-3 py-2 rounded" onClick={() => download('csv')}>CSV</button>
        <button className="bg-gray-700 text-white px-3 py-2 rounded" onClick={() => download('xlsx')}>XLSX</button>
      </div>
    </div>
  )
}