import { useEffect } from 'react'
import { TimeTracker } from './pages/TimeTracker'
import { MyDay } from './pages/MyDay'
import { Reports } from './pages/Reports'
import { Requests } from './pages/Requests'
import { Profile } from './pages/Profile'
import { Admin } from './pages/Admin'
import { useTelegram } from './hooks/useTelegram'

export default function App() {
  const { ready, expand } = useTelegram()

  useEffect(() => { if (ready) expand() }, [ready])

  return (
    <div className="p-4 space-y-4 max-w-xl mx-auto">
      <h1 className="text-xl font-semibold">Учёт времени</h1>
      <TimeTracker />
      <MyDay />
      <Reports />
      <Requests />
      <Profile />
      <Admin />
    </div>
  )
}