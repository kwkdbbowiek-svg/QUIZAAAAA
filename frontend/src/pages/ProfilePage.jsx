import { useState, useEffect } from 'react'
import { useApp } from '../App'
import { api } from '../services/api'

export function ProfilePage() {
  const { user, refreshUser } = useApp()
  const [transactions, setTransactions] = useState([])
  const [showTx, setShowTx] = useState(false)
  const [loading, setLoading] = useState(false)

  const loadTransactions = async () => {
    if (showTx) { setShowTx(false); return }
    setLoading(true)
    try {
      const data = await api.getTransactions()
      setTransactions(data)
      setShowTx(true)
    } finally {
      setLoading(false)
    }
  }

  if (!user) return null

  const levelProgress = getLevelProgress(user.xp_points, user.level)

  return (
    <div className="p-4 max-w-md mx-auto space-y-4">
      {/* Header */}
      <div className="card text-center pt-6">
        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-3xl mx-auto mb-3">
          {(user.first_name || 'U')[0].toUpperCase()}
        </div>
        <h2 className="text-xl font-bold text-white">{user.full_name}</h2>
        {user.username && <p className="text-gray-400 text-sm">@{user.username}</p>}

        {/* Level Badge */}
        <div className="level-badge mx-auto mt-2 w-fit">
          🏅 Daraja {user.level}
        </div>

        {/* XP Progress */}
        <div className="mt-3">
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            <span>XP: {user.xp_points}</span>
            <span>Keyingi daraja: {levelProgress.next}</span>
          </div>
          <div className="w-full h-2 bg-gray-700 rounded-full">
            <div
              className="progress-bar"
              style={{ width: `${levelProgress.percent}%` }}
            />
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3">
        <div className="card text-center">
          <div className="text-2xl font-bold text-green-400">{user.balance.toLocaleString()} so'm</div>
          <div className="text-gray-400 text-sm mt-1">💰 Balans</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-yellow-400">{user.xp_points}</div>
          <div className="text-gray-400 text-sm mt-1">⭐ XP</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-blue-400">{user.total_games}</div>
          <div className="text-gray-400 text-sm mt-1">🎮 O'yinlar</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-purple-400">{user.accuracy}%</div>
          <div className="text-gray-400 text-sm mt-1">🎯 Aniqlik</div>
        </div>
      </div>

      {/* Reyting */}
      <div className="card">
        <h3 className="font-bold text-white mb-3">📊 Reyting O'rnim</h3>
        <div className="space-y-2">
          {[
            { label: '📅 Kunlik', rank: user.daily_rank },
            { label: '📆 Haftalik', rank: user.weekly_rank },
            { label: '🌍 Umumiy', rank: user.global_rank },
          ].map(({ label, rank }) => (
            <div key={label} className="flex justify-between items-center">
              <span className="text-gray-300 text-sm">{label}</span>
              <span className="font-bold text-white">
                {rank ? `${rank}-o'rin` : 'Ro\'yxatda yo\'q'}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Jami yutuqlar */}
      <div className="card bg-gradient-to-r from-blue-900/50 to-purple-900/50">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-gray-400 text-sm">💎 Jami yutuqlar</div>
            <div className="text-2xl font-bold text-white mt-1">
              {user.total_winnings.toLocaleString()} so'm
            </div>
          </div>
          <div className="text-4xl">🏆</div>
        </div>
      </div>

      {/* Balans tarixi */}
      <button onClick={loadTransactions} className="btn-secondary w-full">
        {loading ? '⏳ Yuklanmoqda...' : showTx ? '▲ Yopish' : '💰 Balans tarixi'}
      </button>

      {showTx && transactions.length > 0 && (
        <div className="card space-y-2">
          {transactions.map(tx => (
            <div key={tx.id} className="flex justify-between items-center py-2 border-b border-white/5">
              <div>
                <div className="text-sm text-white">{tx.description || tx.type}</div>
                <div className="text-xs text-gray-400">
                  {new Date(tx.created_at).toLocaleDateString('uz-UZ')}
                </div>
              </div>
              <div className={`font-bold ${tx.amount > 0 ? 'text-green-400' : 'text-red-400'}`}>
                {tx.amount > 0 ? '+' : ''}{tx.amount.toLocaleString()} so'm
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function getLevelProgress(xp, level) {
  const thresholds = [0, 30, 75, 150, 300, 600, 1200, 2500, 5000, 10000, Infinity]
  const current = thresholds[level - 1] || 0
  const next = thresholds[level] || thresholds[thresholds.length - 1]
  const percent = next === Infinity ? 100 : Math.min(100, ((xp - current) / (next - current)) * 100)
  return { percent: Math.round(percent), next }
}
