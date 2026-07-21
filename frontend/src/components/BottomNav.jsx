import { useApp } from '../App'

const navItems = [
  { id: 'profile', icon: '👤', label: 'Profil' },
  { id: 'quiz', icon: '🎯', label: 'Quiz' },
  { id: 'challenge', icon: '🏆', label: 'Challenge' },
  { id: 'leaderboard', icon: '📊', label: 'Reyting' },
]

export function BottomNav() {
  const { activePage, setActivePage, user } = useApp()

  const items = user?.is_admin
    ? [...navItems, { id: 'admin', icon: '⚙️', label: 'Admin' }]
    : navItems

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50"
      style={{ background: 'rgba(26,26,46,0.95)', backdropFilter: 'blur(20px)', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
      <div className="flex justify-around items-center py-2 px-2 max-w-md mx-auto">
        {items.map(item => (
          <button
            key={item.id}
            onClick={() => setActivePage(item.id)}
            className={`flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-xl transition-all ${
              activePage === item.id
                ? 'text-blue-400'
                : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            <span className="text-xl">{item.icon}</span>
            <span className="text-xs">{item.label}</span>
            {activePage === item.id && (
              <div className="w-1 h-1 bg-blue-400 rounded-full mt-0.5" />
            )}
          </button>
        ))}
      </div>
    </nav>
  )
}
