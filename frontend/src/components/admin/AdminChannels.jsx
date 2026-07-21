import { useState, useEffect } from 'react'
import { api } from '../../services/api'

export default function AdminChannels() {
  const [channels, setChannels] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ channel_id: '', channel_name: '', channel_link: '' })
  const [msg, setMsg] = useState('')

  useEffect(() => { load() }, [])

  const load = async () => {
    try { setChannels(await api.getChannels()) }
    catch (e) { console.error(e) }
  }

  const add = async (e) => {
    e.preventDefault()
    try {
      await api.addChannel(form)
      setMsg('✅ Kanal qo\'shildi!')
      setForm({ channel_id: '', channel_name: '', channel_link: '' })
      setShowForm(false)
      load()
    } catch (e) { setMsg('Xato: ' + e.message) }
  }

  const toggle = async (id) => {
    try { await api.toggleChannel(id); load() }
    catch (e) { setMsg('Xato: ' + e.message) }
  }

  const remove = async (id) => {
    if (!confirm('Kanalni o\'chirish?')) return
    try { await api.deleteChannel(id); load() }
    catch (e) { setMsg('Xato: ' + e.message) }
  }

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <h2 className="text-white font-bold">📢 Majburiy Kanallar</h2>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary px-4 py-2 text-sm">
          {showForm ? '✕' : '➕ Qo\'shish'}
        </button>
      </div>
      {msg && <div className="card text-center text-sm text-green-400">{msg}</div>}

      {showForm && (
        <form onSubmit={add} className="card space-y-3">
          {[
            { key: 'channel_id',   placeholder: 'Kanal ID (@username yoki -100...)',  required: true },
            { key: 'channel_name', placeholder: 'Kanal nomi *', required: true },
            { key: 'channel_link', placeholder: 'Kanal linki (ixtiyoriy)' },
          ].map(({ key, placeholder, required }) => (
            <input key={key} type="text" placeholder={placeholder} required={required}
              value={form[key]} onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
              className="w-full p-3 rounded-xl bg-white/10 text-white border border-white/10 outline-none text-sm" style={{ userSelect: 'text' }} />
          ))}
          <button type="submit" className="btn-primary w-full">✅ Saqlash</button>
        </form>
      )}

      <div className="space-y-2">
        {channels.map(ch => (
          <div key={ch.id} className="card flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full flex-shrink-0 ${ch.is_active ? 'bg-green-400' : 'bg-gray-500'}`} />
            <div className="flex-1 min-w-0">
              <div className="text-white font-medium text-sm truncate">{ch.channel_name}</div>
              <div className="text-gray-400 text-xs truncate">{ch.channel_id}</div>
            </div>
            <div className="flex gap-2 flex-shrink-0">
              <button onClick={() => toggle(ch.id)}
                className={`px-3 py-1 rounded-lg text-xs font-bold ${ch.is_active ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'}`}>
                {ch.is_active ? 'O\'ch' : 'Yoq'}
              </button>
              <button onClick={() => remove(ch.id)} className="px-3 py-1 rounded-lg text-xs bg-white/10 text-gray-400">🗑</button>
            </div>
          </div>
        ))}
        {channels.length === 0 && <div className="card text-center text-gray-400 py-6">Hali kanallar qo'shilmagan</div>}
      </div>
    </div>
  )
}
