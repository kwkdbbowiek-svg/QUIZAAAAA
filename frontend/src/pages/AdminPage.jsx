import { useState, useEffect } from 'react'
import { useApp } from '../App'
import AdminDashboard from '../components/admin/AdminDashboard'
import AdminUsers from '../components/admin/AdminUsers'
import AdminQuestions from '../components/admin/AdminQuestions'
import AdminChallenges from '../components/admin/AdminChallenges'
import AdminChannels from '../components/admin/AdminChannels'
import AdminBroadcast from '../components/admin/AdminBroadcast'

const TABS = [
  { id: 'dashboard',  icon: '📊', label: 'Stat' },
  { id: 'users',      icon: '👥', label: 'Userlar' },
  { id: 'questions',  icon: '❓', label: 'Savollar' },
  { id: 'challenges', icon: '🏆', label: 'Challenge' },
  { id: 'channels',   icon: '📢', label: 'Kanallar' },
  { id: 'broadcast',  icon: '📣', label: 'Broadcast' },
]

export function AdminPage() {
  const { user } = useApp()
  const [tab, setTab] = useState('dashboard')

  if (user && !user.is_admin) {
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
    <div className="min-h-screen">
      <div className="sticky top-0 z-40 px-3 pt-3 pb-2"
        style={{ background: 'rgba(15,15,35,0.97)', backdropFilter: 'blur(12px)', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
        <div className="flex justify-between items-center mb-2">
          <h1 className="text-base font-bold text-white">⚙️ Admin Panel</h1>
          {user && <span className="text-xs text-gray-400">@{user.username || 'admin'}</span>}
        </div>
        <div className="flex gap-1.5 overflow-x-auto no-scrollbar">
          {TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`flex-shrink-0 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                tab === t.id ? 'bg-blue-500 text-white' : 'bg-white/10 text-gray-400 hover:bg-white/15'
              }`}>
              {t.icon} {t.label}
            </button>
          ))}
        </div>
      </div>
      <div className="px-3 pt-3 pb-20">{panels[tab]}</div>
    </div>
  )
}
