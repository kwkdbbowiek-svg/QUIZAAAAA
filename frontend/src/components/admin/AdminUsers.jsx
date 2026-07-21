import { useState } from 'react'
import { api } from '../../services/api'

export default function AdminUsers() {
  const [query, setQuery] = useState('')
  const [users, setUsers] = useState([])
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(false)
  const [balanceForm, setBalanceForm] = useState({ amount: '', operation: 'add', note: '' })
  const [msg, setMsg] = useState('')

  const search = async () => {
    if (!query.trim()) return
    setLoading(true)
    try { setUsers(await api.searchUsers(query)) }
    finally { setLoading(false) }
  }

  const adjustBalance = async () => {
    if (!balanceForm.amount) return
    try {
      const res = await api.adjustBalance(selected.id, +balanceForm.amount, balanceForm.operation, balanceForm.note)
      setMsg(res.message)
      setSelected({ ...selected, balance: res.new_balance })
      setBalanceForm({ amount: '', operation: 'add', note: '' })
    } catch (e) { setMsg('Xato: ' + e.message) }
  }

  const changeStatus = async (status) => {
    try {
      await api.request(`/api/users/admin/${selected.id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) })
      setMsg('Status o\'zgartirildi')
      setSelected({ ...selected, status })
    } catch (e) { setMsg('Xato: ' + e.message) }
  }

  if (selected) return (
    <div className="space-y-3">
      <button onClick={() => { setSelected(null); setMsg('') }} className="text-blue-400 flex items-center gap-1 text-sm">◀️ Orqaga</button>
      <div className="card space-y-2">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg">
            {selected.first_name?.[0]?.toUpperCase()}
          </div>
          <div>
            <div className="font-bold text-white">{selected.full_name}</div>
            <div className="text-gray-400 text-sm">@{selected.username || 'yo\'q'} · ID: {selected.telegram_id}</div>
          </div>
        </div>
        {[
          ['💰 Balans', `${selected.balance?.toLocaleString()} so'm`],
          ['⭐ XP', selected.xp_points],
          ['🏅 Daraja', selected.level],
          ['🎮 O\'yinlar', selected.total_games],
          ['📊 Status', selected.status],
          ['📱 Telefon', selected.phone_number || 'yo\'q'],
        ].map(([k, v]) => (
          <div key={k} className="flex justify-between py-1 border-b border-white/5">
            <span className="text-gray-400 text-sm">{k}</span>
            <span className="text-white text-sm font-medium">{v}</span>
          </div>
        ))}
      </div>

      <div className="card space-y-2">
        <h3 className="font-bold text-white text-sm">💰 Balans sozlash</h3>
        <div className="flex gap-2">
          <button onClick={() => setBalanceForm(f => ({ ...f, operation: 'add' }))}
            className={`flex-1 py-2 rounded-xl text-sm font-bold ${balanceForm.operation === 'add' ? 'bg-green-500 text-white' : 'bg-white/10 text-gray-400'}`}>+ Qo'shish</button>
          <button onClick={() => setBalanceForm(f => ({ ...f, operation: 'subtract' }))}
            className={`flex-1 py-2 rounded-xl text-sm font-bold ${balanceForm.operation === 'subtract' ? 'bg-red-500 text-white' : 'bg-white/10 text-gray-400'}`}>- Ayirish</button>
        </div>
        <input type="number" placeholder="Miqdor (so'm)" value={balanceForm.amount}
          onChange={e => setBalanceForm(f => ({ ...f, amount: e.target.value }))}
          className="w-full p-3 rounded-xl bg-white/10 text-white border border-white/10 outline-none" style={{ userSelect: 'text' }} />
        <input type="text" placeholder="Izoh (ixtiyoriy)" value={balanceForm.note}
          onChange={e => setBalanceForm(f => ({ ...f, note: e.target.value }))}
          className="w-full p-3 rounded-xl bg-white/10 text-white border border-white/10 outline-none" style={{ userSelect: 'text' }} />
        <button onClick={adjustBalance} className="btn-primary w-full">Saqlash</button>
      </div>

      <div className="card space-y-2">
        <h3 className="font-bold text-white text-sm">⚙️ Status</h3>
        <div className="flex gap-2">
          <button onClick={() => changeStatus('active')} className="flex-1 py-2 rounded-xl text-sm bg-green-500/20 text-green-400 font-bold">✅ Faollashtirish</button>
          <button onClick={() => changeStatus('banned')} className="flex-1 py-2 rounded-xl text-sm bg-red-500/20 text-red-400 font-bold">🚫 Bloklash</button>
        </div>
      </div>
      {msg && <div className="card text-center text-green-400 text-sm">{msg}</div>}
    </div>
  )

  return (
    <div className="space-y-3">
      <h2 className="text-white font-bold">👥 Foydalanuvchilar</h2>
      <div className="flex gap-2">
        <input type="text" placeholder="ID, username yoki ism..." value={query}
          onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && search()}
          className="flex-1 p-3 rounded-xl bg-white/10 text-white border border-white/10 outline-none text-sm" style={{ userSelect: 'text' }} />
        <button onClick={search} className="btn-primary px-4">🔍</button>
      </div>
      {loading && <div className="text-center text-gray-400 py-4">Qidirilmoqda...</div>}
      <div className="space-y-2">
        {users.map(u => (
          <div key={u.id} onClick={() => setSelected(u)} className="card flex items-center gap-3 cursor-pointer hover:bg-white/10 transition-all">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold flex-shrink-0">
              {u.first_name?.[0]?.toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-white font-medium truncate">{u.full_name}</div>
              <div className="text-gray-400 text-xs">@{u.username || 'yo\'q'} · {u.balance?.toLocaleString()} so'm</div>
            </div>
            <div className={`text-xs px-2 py-0.5 rounded-full ${u.status === 'active' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
              {u.status}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
