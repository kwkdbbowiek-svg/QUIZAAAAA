import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { useApp } from '../App'

export function LeaderboardPage() {
  const { user } = useApp()
  const [activeBoard, setActiveBoard] = useState('global')
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadLeaderboard()
  }, [activeBoard])

  const loadLeaderboard = async () => {
    setLoading(true)
    try {
      const res = await api.getLeaderboard(activeBoard, 50)
      setData(res)
    } finally {
      setLoading(false)
    }
  }

  const boards = [
    { id: 'daily', label: '📅 Kunlik' },
    { id: 'weekly', label: '📆 Haftalik' },
    { id: 'global', label: '🌍 Umumiy' },
  ]

  const medals = { 1: '🥇', 2: '🥈', 3: '🥉' }

  return (
    <div className="p-4 max-w-md mx-auto">
      <h1 className="text-xl font-bold text-white mb-4">📊 Reyting</h1>

      {/* Board Selector */}
      <div className="flex gap-2 mb-4">
        {boards.map(b => (
          <button key={b.id} onClick={() => setActiveBoard(b.id)}
            className={`flex-1 py-2 rounded-xl text-sm font-medium transition-all ${
              activeBoard === b.id ? 'bg-blue-500 text-white' : 'bg-white/5 text-gray-400'
            }`}>
            {b.label}
          </button>
        ))}
      </div>

      <button onClick={loadLeaderboard}
        className="w-full py-2 rounded-xl bg-white/5 text-gray-400 text-sm mb-4">
        🔄 Yangilash
      </button>

      {loading && (
        <div className="flex justify-center py-8">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {!loading && data.length === 0 && (
        <div className="card text-center py-8">
          <p className="text-gray-400">Hali ma'lumot yo'q</p>
        </div>
      )}

      {!loading && data.length > 0 && (
        <div className="space-y-2">
          {data.map(entry => {
            const isMe = entry.telegram_id === user?.telegram_id
            return (
              <div key={entry.user_id}
                className={`card flex items-center gap-3 transition-all ${
                  isMe ? 'border border-blue-500 bg-blue-900/20' : ''
                }`}>
                {/* Rank */}
                <div className="w-10 text-center">
                  {medals[entry.rank] ? (
                    <span className="text-2xl">{medals[entry.rank]}</span>
                  ) : (
                    <span className="text-gray-400 font-bold text-sm">{entry.rank}</span>
                  )}
                </div>

                {/* Avatar */}
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center text-white font-bold flex-shrink-0">
                  {entry.full_name[0].toUpperCase()}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-white truncate">
                    {entry.full_name}
                    {isMe && <span className="ml-1 text-xs text-blue-400">(Siz)</span>}
                  </div>
                  {entry.username && (
                    <div className="text-xs text-gray-500">@{entry.username}</div>
                  )}
                </div>

                {/* Score & Level */}
                <div className="text-right flex-shrink-0">
                  <div className="font-bold text-yellow-400 text-sm">{entry.score} XP</div>
                  <div className="text-xs text-gray-500">Daraja {entry.level}</div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
