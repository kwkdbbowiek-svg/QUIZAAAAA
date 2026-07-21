import { useState } from 'react'
import { api } from '../../services/api'

export default function AdminUsers() {
  const [query, setQuery] = useState('')
  const [users, setUsers] = useState([])
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(false)
  const [msg, setMsg] = useState('')
  const [balance, setBalance] = useState({ amount: '', operation: 'add', note: '' })

  const search = async () => {
    if (!query.trim()) return
    setLoading(true)
    setMsg('')
    try {
      const data = await api.searchUsers(query)
      setUsers(data)
    } catch (e) { setMsg('❌ ' + e.message) }
    finally { setLoading(false) }
  }

  const adjustBalance = async () => {
    if (!balance.amount || isNaN(+balance.amount)) { setMsg('❌ Miqdor kiriting'); return }
    try {
      const res = await api.adjustBalance(selected.id, +balance.amount, balance.operation, balance.note)
      setMsg('✅ Balans yangilandi: ' + res.new_balance?.toLocaleString() + " so'm")
      setSelected(s => ({ ...s, balance: res.new_balance }))
      setBalance({ amount: '', operation: 'add', note: '' })
    } catch (e) { setMsg('❌ ' + e.message) }
  }

  const changeStatus = async (status) => {
    try {
      await api.request(`/api/admin/users/${selected.id}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status })
      })
      setMsg('✅ Status: ' + status)
      setSelected(s => ({ ...s, status }))
    } catch (e) { setMsg('❌ ' + e.message) }
  }

  if (selected) return (
    <div className="space-y-3">
      <button onClick={() => { setSelected(null); setMsg('') }} className="text-blue-400 text-sm flex items-center gap-1">◀️ Orqaga</button>
      <div className="card">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg flex-shrink-0">
            {(selected.first_name || 'U')[0].toUpperCase()}
          </div>
          <div>
            <div className="font-bold text-white">{selected.full_name}</div>
            <div className="text-gray-400 text-xs">@{selected.username || 'yo\'q'} · {selected.telegram_id}</div>
          </div>
        </div>
        <div className="mt-3 space-y-1">
          {[
            ['💰 Balans', `${(selected.balance||0).toLocaleString()} so'm`],
            ['⭐ XP',     selected.xp_points || 0],
            ['🏅 Daraja', selected.level || 1],
            ['🎮 O\'yinlar', selected.total_games || 0],
            ['🎯 Aniqlik', `${selected.accuracy || 0}%`],
            ['📊 Status',  selected.status],
            ['📱 Telefon', selected.phone_number || 'yo\'q'],
          ].map(([k, v]) => (
            <div key={k} className="flex justify-between py-1 border-b border-white/5 last:border-0">
              <span className="text-gray-400 text-sm">{k}</span>
              <span className="text-white text-sm font-medium">{String(v)}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="card space-y-2">
        <h3 className="text-white font-bold text-sm">💰 Balans sozlash</h3>
        <div className="flex gap-2">
          <button onClick={() => setBalance(b => ({ ...b, operation: 'add' }))}
            className={`flex-1 py-2 rounded-xl text-sm font-bold transition-all ${balance.operation === 'add' ? 'bg-green-500 text-white' : 'bg-white/10 text-gray-400'}`}>
            ➕ Qo'shish
          </button>
          <button onClick={() => setBalance(b => ({ ...b, operation: 'subtract' }))}
            className={`flex-1 py-2 rounded-xl text-sm font-bold transition-all ${balance.operation === 'subtract' ? 'bg-red-500 text-white' : 'bg-white/10 text-gray-400'}`}>
            ➖ Ayirish
          </button>
        </div>
        <input type="number" placeholder="Miqdor (so'm)" value={balance.amount}
          onChange={e => setBalance(b => ({ ...b, amount: e.target.value }))}
          className="w-full p-3 rounded-xl bg-white/10 text-white border border-white/10 outline-none text-sm" style={{ userSelect: 'text' }} />
        <input type="text" placeholder="Izoh (ixtiyoriy)" value={balance.note}
          onChange={e => setBalance(b => ({ ...b, note: e.target.value }))}
          className="w-full p-2 rounded-xl bg-white/10 text-white border border-white/10 outline-none text-sm" style={{ userSelect: 'text' }} />
        <button onClick={adjustBalance} className="btn-primary w-full py-2">Saqlash</button>
      </div>

      <div className="card space-y-2">
        <h3 className="text-white font-bold text-sm">⚙️ Status o'zgartirish</h3>
        <div className="flex gap-2">
          <button onClick={() => changeStatus('active')} className="flex-1 py-2 rounded-xl text-sm bg-green-500/20 text-green-400 font-bold">✅ Faollashtirish</button>
          <button onClick={() => changeStatus('banned')} className="flex-1 py-2 rounded-xl text-sm bg-red-500/20 text-red-400 font-bold">🚫 Bloklash</button>
        </div>
      </div>

      {msg && <div className={`card text-center text-sm ${msg.startsWith('✅') ? 'text-green-400' : 'text-red-400'}`}>{msg}</div>}
    </div>
  )

  return (
    <div className="space-y-3">
      <h2 className="text-white font-bold">👥 Foydalanuvchilar</h2>
      <div className="flex gap-2">
        <input type="text" placeholder="Telegram ID, username yoki ism..."
          value={query} onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && search()}
          className="flex-1 p-3 rounded-xl bg-white/10 text-white border border-white/10 outline-none text-sm" style={{ userSelect: 'text' }} />
        <button onClick={search} className="btn-primary px-4">🔍</button>
      </div>
      {msg && <div className={`card text-center text-sm ${msg.startsWith('✅') ? 'text-green-400' : 'text-red-400'}`}>{msg}</div>}
      {loading && <div className="text-center text-gray-400 py-4 text-sm">Qidirilmoqda...</div>}
      <div className="space-y-2">
        {users.map(u => (
          <div key={u.id} onClick={() => { setSelected(u); setMsg('') }}
            className="card flex items-center gap-3 cursor-pointer hover:bg-white/10 transition-all active:scale-99">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold flex-shrink-0">
              {(u.first_name || 'U')[0].toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-white font-medium truncate text-sm">{u.full_name}</div>
              <div className="text-gray-400 text-xs">@{u.username || 'yo\'q'} · {(u.balance || 0).toLocaleString()} so'm</div>
            </div>
            <span className={`text-xs px-2 py-0.5 rounded-full flex-shrink-0 ${u.status === 'active' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
              {u.status}
            </span>
          </div>
        ))}
        {!loading && users.length === 0 && query && (
          <div className="card text-center text-gray-400 py-4 text-sm">Topilmadi</div>
        )}
      </div>
    </div>
  )
}
