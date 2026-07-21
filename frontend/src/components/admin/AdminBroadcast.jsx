import { useState, useEffect } from 'react'
import { api } from '../../services/api'

export default function AdminBroadcast() {
  const [form, setForm] = useState({ message_type: 'text', text: '', button_text: '', button_url: '' })
  const [sending, setSending] = useState(false)
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])
  const [msg, setMsg] = useState('')

  useEffect(() => { loadHistory() }, [])

  const loadHistory = async () => {
    try { setHistory(await api.request('/api/admin/broadcasts')) }
    catch (e) { console.error(e) }
  }

  const send = async (e) => {
    e.preventDefault()
    if (!form.text.trim()) { setMsg('Xabar matnini kiriting'); return }
    if (!confirm('Barcha foydalanuvchilarga yuborishni tasdiqlaysizmi?')) return
    setSending(true)
    try {
      const res = await api.sendBroadcast(form)
      setResult(res)
      setMsg(`✅ Broadcast yaratildi! ${res.total_recipients} ta foydalanuvchiga yuboriladi.`)
      setForm({ message_type: 'text', text: '', button_text: '', button_url: '' })
      setTimeout(loadHistory, 3000)
    } catch (e) { setMsg('Xato: ' + e.message) }
    finally { setSending(false) }
  }

  return (
    <div className="space-y-4">
      <h2 className="text-white font-bold">📣 Broadcast</h2>
      {msg && <div className="card text-center text-sm text-green-400">{msg}</div>}

      <form onSubmit={send} className="card space-y-3">
        <h3 className="font-bold text-white text-sm">Yangi xabar</h3>
        <select value={form.message_type} onChange={e => setForm(f => ({ ...f, message_type: e.target.value }))}
          className="w-full p-3 rounded-xl bg-white/10 text-white border border-white/10 outline-none text-sm">
          <option value="text">📝 Matn</option>
          <option value="photo">🖼 Rasm + Matn</option>
          <option value="video">🎥 Video + Matn</option>
        </select>

        <textarea placeholder="Xabar matni (HTML qo'llab-quvvatlanadi: <b>, <i>, <code>)" required
          rows={5} value={form.text} onChange={e => setForm(f => ({ ...f, text: e.target.value }))}
          className="w-full p-3 rounded-xl bg-white/10 text-white border border-white/10 outline-none resize-none text-sm" style={{ userSelect: 'text' }} />

        <div className="grid grid-cols-1 gap-2">
          <input type="text" placeholder="Tugma matni (ixtiyoriy)"
            value={form.button_text} onChange={e => setForm(f => ({ ...f, button_text: e.target.value }))}
            className="w-full p-2 rounded-xl bg-white/10 text-white border border-white/10 outline-none text-sm" style={{ userSelect: 'text' }} />
          <input type="url" placeholder="Tugma URL (ixtiyoriy)"
            value={form.button_url} onChange={e => setForm(f => ({ ...f, button_url: e.target.value }))}
            className="w-full p-2 rounded-xl bg-white/10 text-white border border-white/10 outline-none text-sm" style={{ userSelect: 'text' }} />
        </div>

        <button type="submit" disabled={sending}
          className="btn-primary w-full py-3 text-base font-bold disabled:opacity-50">
          {sending ? '📤 Yuborilmoqda...' : '📣 Barcha Foydalanuvchilarga Yuborish'}
        </button>
      </form>

      {history.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-white font-bold text-sm">📋 Broadcast tarixi</h3>
          {history.slice(0, 10).map(b => (
            <div key={b.id} className="card">
              <div className="flex justify-between items-center">
                <div className="text-white text-sm truncate flex-1 mr-2">{b.text?.slice(0, 50) || '(media)'}</div>
                <span className={`text-xs px-2 py-0.5 rounded-full flex-shrink-0 ${
                  b.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                  b.status === 'sending'   ? 'bg-yellow-500/20 text-yellow-400' :
                  'bg-gray-500/20 text-gray-400'
                }`}>{b.status}</span>
              </div>
              <div className="text-xs text-gray-500 mt-1">
                📨 {b.total_sent} · ✅ {b.success_count} · ❌ {b.failed_count}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
