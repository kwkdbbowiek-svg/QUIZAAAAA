import { useState, useEffect } from 'react'
import { api } from '../../services/api'

export default function AdminDashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => { load() }, [])

  const load = async () => {
    setLoading(true)
    try { setStats(await api.getAdminStats()) }
    finally { setLoading(false) }
  }

  if (loading) return <Loader />

  const cards = [
    { icon: '👥', label: 'Jami foydalanuvchilar', value: stats?.total_users ?? 0, color: 'from-blue-600 to-blue-400' },
    { icon: '🆕', label: 'Bugun qo\'shildi',       value: stats?.new_users_today ?? 0, color: 'from-green-600 to-green-400' },
    { icon: '🟢', label: 'Kunlik faollar',          value: stats?.daily_active_users ?? 0, color: 'from-teal-600 to-teal-400' },
    { icon: '🏆', label: 'Faol challengelar',        value: stats?.active_challenges ?? 0, color: 'from-yellow-600 to-yellow-400' },
    { icon: '💰', label: 'Jami balanslar',           value: `${(stats?.total_balance ?? 0).toLocaleString()} so'm`, color: 'from-purple-600 to-purple-400' },
    { icon: '📈', label: 'Haftalik daromad',         value: `${(stats?.weekly_income ?? 0).toLocaleString()} so'm`, color: 'from-pink-600 to-pink-400' },
  ]

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <h2 className="text-white font-bold">📊 Dashboard</h2>
        <button onClick={load} className="text-blue-400 text-sm">🔄 Yangilash</button>
      </div>
      <div className="grid grid-cols-2 gap-3">
        {cards.map(c => (
          <div key={c.label} className={`rounded-2xl p-4 bg-gradient-to-br ${c.color} text-white shadow-lg`}>
            <div className="text-2xl mb-1">{c.icon}</div>
            <div className="text-xl font-bold">{c.value}</div>
            <div className="text-xs opacity-80 mt-0.5">{c.label}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function Loader() {
  return <div className="flex justify-center py-12"><div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"/></div>
}
