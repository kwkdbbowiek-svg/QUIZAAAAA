import { useState, useEffect } from 'react'
import { useApp } from '../App'
import { api } from '../services/api'

// ─── Tab komponentlari ────────────────────────────────────────────────────────
import AdminDashboard from '../components/admin/AdminDashboard'
import AdminUsers from '../components/admin/AdminUsers'
import AdminQuestions from '../components/admin/AdminQuestions'
import AdminChallenges from '../components/admin/AdminChallenges'
import AdminChannels from '../components/admin/AdminChannels'
import AdminBroadcast from '../components/admin/AdminBroadcast'

const TABS = [
  { id: 'dashboard',  icon: '📊', label: 'Statistika' },
  { id: 'users',      icon: '👥', label: 'Userlar' },
  { id: 'questions',  icon: '❓', label: 'Savollar' },
  { id: 'challenges', icon: '🏆', label: 'Challenge' },
  { id: 'channels',   icon: '📢', label: 'Kanallar' },
  { id: 'broadcast',  icon: '📣', label: 'Broadcast' },
]

export function AdminPage() {
  const { user } = useApp()
  const [tab, setTab] = useState('dashboard')

  if (!user?.is_admin) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="card text-center p-8">
          <div className="text-5xl mb-3">⛔</div>
          <p className="text-white font-bold">Admin huquqlari kerak</p>
        </div>
      </div>
    )
  }

  const panels = {
    dashboard:  <AdminDashboard />,
    users:      <AdminUsers />,
    questions:  <AdminQuestions />,
    challenges: <AdminChallenges />,
    channels:   <AdminChannels />,
    broadcast:  <AdminBroadcast />,
  }

  return (
    <div className="min-h-screen pb-4">
      <div className="sticky top-0 z-40 px-3 pt-3 pb-2"
        style={{ background: 'rgba(26,26,46,0.97)', backdropFilter: 'blur(12px)' }}>
        <h1 className="text-lg font-bold text-white mb-2">⚙️ Admin Panel</h1>
        <div className="flex gap-1.5 overflow-x-auto no-scrollbar pb-1">
          {TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`flex-shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                tab === t.id ? 'bg-blue-500 text-white' : 'bg-white/10 text-gray-400'
              }`}>
              {t.icon} {t.label}
            </button>
          ))}
        </div>
      </div>
      <div className="px-3 pt-2">{panels[tab]}</div>
    </div>
  )
}
