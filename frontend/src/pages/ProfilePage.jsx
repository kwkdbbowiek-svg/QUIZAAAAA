import { useState, useEffect } from 'react'
import { useApp } from '../App'
import { api } from '../services/api'

export function ProfilePage() {
  const { user, setUser, setActivePage } = useApp()
  const [profile, setProfile] = useState(null)
  const [transactions, setTransactions] = useState([])
  const [showTx, setShowTx] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadProfile()
  }, [])

  const loadProfile = async () => {
    setLoading(true)
    try {
      const data = await api.getProfile()
      setProfile(data)
      setUser(prev => ({ ...(prev || {}), ...data }))
    } catch (e) {
      console.error('Profil xatosi:', e)
      // user context'dan olish
      if (user) setProfile(user)
    } finally {
      setLoading(false)
    }
  }

  const loadTransactions = async () => {
    if (showTx) { setShowTx(false); return }
    try {
      const data = await api.getTransactions()
      setTransactions(data)
      setShowTx(true)
    } catch (e) { console.error(e) }
  }

  const p = profile || user

  if (!p && loading) return (
    <div className="flex justify-center items-center h-64">
      <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  if (!p) return (
    <div className="flex justify-center items-center h-64">
      <div className="card text-center p-6">
        <div className="text-3xl mb-2">⚠️</div>
        <p className="text-gray-400 text-sm">Profil yuklanmadi</p>
        <button onClick={loadProfile} className="btn-primary px-4 py-2 text-sm mt-3">🔄 Qayta urinish</button>
      </div>
    </div>
  )

  const levelProgress = getLevelProgress(p.xp_points || 0, p.level || 1)

  return (
    <div className="p-4 max-w-md mx-auto space-y-4">

      {/* Header */}
      <div className="card text-center pt-5 pb-4">
        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-3xl mx-auto mb-3 shadow-lg">
          {(p.first_name || 'U')[0].toUpperCase()}
        </div>
        <h2 className="text-xl font-bold text-white">{p.full_name || p.first_name || 'Foydalanuvchi'}</h2>
        {p.username && <p className="text-gray-400 text-sm mt-0.5">@{p.username}</p>}
        <div className="level-badge mx-auto mt-2 w-fit">🏅 Daraja {p.level || 1}</div>

        <div className="mt-3 px-2">
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            <span>XP: {p.xp_points || 0}</span>
            <span>Keyingi: {levelProgress.next}</span>
          </div>
          <div className="w-full h-2 bg-gray-700 rounded-full">
            <div className="progress-bar" style={{ width: `${levelProgress.percent}%` }} />
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3">
        {[
          { label: '💰 Balans', value: `${(p.balance || 0).toLocaleString()} so'm`, color: 'text-green-400' },
          { label: '⭐ XP',     value: p.xp_points || 0,  color: 'text-yellow-400' },
          { label: '🎮 O\'yinlar', value: p.total_games || 0, color: 'text-blue-400' },
          { label: '🎯 Aniqlik', value: `${p.accuracy || 0}%`, color: 'text-purple-400' },
        ].map(({ label, value, color }) => (
          <div key={label} className="card text-center py-3">
            <div className={`text-xl font-bold ${color}`}>{value}</div>
            <div className="text-gray-400 text-xs mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Reyting */}
      <div className="card">
        <div className="flex justify-between items-center mb-2">
          <h3 className="font-bold text-white text-sm">📊 Reytingim</h3>
          <button onClick={() => setActivePage('leaderboard')} className="text-blue-400 text-xs">Ko'rish →</button>
        </div>
        <div className="space-y-1.5">
          {[
            { label: '📅 Kunlik',  rank: p.daily_rank },
            { label: '📆 Haftalik', rank: p.weekly_rank },
            { label: '🌍 Umumiy',  rank: p.global_rank },
          ].map(({ label, rank }) => (
            <div key={label} className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">{label}</span>
              <span className="font-bold text-white text-sm">
                {rank ? `${rank}-o'rin` : 'Ro\'yxatda yo\'q'}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Jami yutuqlar */}
      {(p.total_winnings || 0) > 0 && (
        <div className="card bg-gradient-to-r from-blue-900/50 to-purple-900/50">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-gray-400 text-xs">💎 Jami yutuqlar</div>
              <div className="text-xl font-bold text-white mt-0.5">
                {(p.total_winnings || 0).toLocaleString()} so'm
              </div>
            </div>
            <div className="text-3xl">🏆</div>
          </div>
        </div>
      )}

      {/* Balans tarixi */}
      <button onClick={loadTransactions} className="btn-secondary w-full">
        {showTx ? '▲ Yopish' : '💰 Balans tarixi'}
      </button>

      {showTx && (
        <div className="card space-y-2">
          {transactions.length === 0
            ? <p className="text-center text-gray-400 text-sm py-2">Hali tranzaksiyalar yo'q</p>
            : transactions.map(tx => {
              const typeEmoji = {
                deposit: '➕', withdraw: '➖', challenge_entry: '🎮',
                challenge_win: '🏆', refund: '↩️', admin_adjust: '⚙️',
              }
              const t = tx.type?.value || tx.type || ''
              const emoji = typeEmoji[t] || '•'
              const sign = tx.amount > 0 ? '+' : ''
              return (
                <div key={tx.id} className="flex justify-between items-center py-1.5 border-b border-white/5 last:border-0">
                  <div>
                    <div className="text-sm text-white">{tx.description || t}</div>
                    <div className="text-xs text-gray-500">
                      {tx.created_at ? new Date(tx.created_at).toLocaleDateString('uz-UZ') : ''}
                    </div>
                  </div>
                  <div className={`font-bold text-sm ${tx.amount > 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {emoji} {sign}{(tx.amount || 0).toLocaleString()} so'm
                  </div>
                </div>
              )
            })
          }
        </div>
      )}

      {/* Yangilash */}
      <button onClick={loadProfile} className="text-gray-500 text-xs w-full text-center hover:text-gray-300">
        🔄 Yangilash
      </button>
    </div>
  )
}

function getLevelProgress(xp, level) {
  const thresholds = [0, 30, 75, 150, 300, 600, 1200, 2500, 5000, 10000, Infinity]
  const current = thresholds[level - 1] || 0
  const next = thresholds[level] || Infinity
  const percent = next === Infinity ? 100 : Math.min(100, ((xp - current) / (next - current)) * 100)
  return { percent: Math.round(percent), next: next === Infinity ? 'Max' : next }
}
