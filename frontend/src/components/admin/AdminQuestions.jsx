import { useState, useEffect } from 'react'
import { api } from '../../services/api'

export default function AdminQuestions() {
  const [questions, setQuestions] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [showCatForm, setShowCatForm] = useState(false)
  const [catForm, setCatForm] = useState({ name: '', icon: '📚', description: '' })
  const [msg, setMsg] = useState('')
  const [form, setForm] = useState({
    text: '', difficulty: 'medium', category_id: '', explanation: '',
    options: [
      { text: '', is_correct: true },
      { text: '', is_correct: false },
      { text: '', is_correct: false },
      { text: '', is_correct: false },
    ]
  })

  useEffect(() => {
    loadCategories()
    loadQuestions()
  }, [])

  const loadCategories = async () => {
    try {
      const data = await api.getCategories()
      setCategories(Array.isArray(data) ? data : [])
    } catch (e) { console.error(e) }
  }

  const addCategory = async (e) => {
    e.preventDefault()
    if (!catForm.name.trim()) return
    try {
      await api.request('/api/admin/categories', {
        method: 'POST',
        body: JSON.stringify(catForm),
      })
      setMsg('✅ Kategoriya qo\'shildi!')
      setCatForm({ name: '', icon: '📚', description: '' })
      setShowCatForm(false)
      loadCategories()
    } catch (e) { setMsg('❌ ' + (e?.message || String(e))) }
  }

  const loadQuestions = async () => {
    setLoading(true)
    try {
      const data = await api.getQuestions({ page: 1, limit: 50 })
      setQuestions(Array.isArray(data) ? data : [])
    } catch (e) {
      setMsg('❌ Savollarni yuklab bo\'lmadi: ' + (e?.message || String(e)))
    } finally {
      setLoading(false)
    }
  }

  const handleOption = (idx, field, val) => {
    setForm(f => ({
      ...f,
      options: f.options.map((o, i) =>
        field === 'is_correct' ? { ...o, is_correct: i === idx } : i === idx ? { ...o, text: val } : o
      )
    }))
  }

  const submit = async (e) => {
    e.preventDefault()
    if (form.options.some(o => !o.text.trim())) { setMsg('❌ Barcha javob variantlarini to\'ldiring'); return }
    if (!form.options.some(o => o.is_correct)) { setMsg('❌ Kamida 1 ta to\'g\'ri javob belgilang'); return }
    try {
      await api.createQuestion({
        text: form.text,
        difficulty: form.difficulty,
        question_type: 'text',
        category_id: form.category_id ? +form.category_id : null,
        options: form.options,
        explanation: form.explanation || null,
      })
      setMsg('✅ Savol qo\'shildi!')
      setShowForm(false)
      setForm({ text: '', difficulty: 'medium', category_id: '', explanation: '', options: [{ text: '', is_correct: true }, { text: '', is_correct: false }, { text: '', is_correct: false }, { text: '', is_correct: false }] })
      loadQuestions()
    } catch (e) {
      const errMsg = e?.message || (typeof e === 'object' ? JSON.stringify(e) : String(e))
      setMsg('❌ ' + errMsg)
    }
  }

  const deleteQ = async (id) => {
    if (!confirm('Savolni o\'chirish?')) return
    try { await api.request(`/api/admin/questions/${id}`, { method: 'DELETE' }); loadQuestions() }
    catch (e) { setMsg('Xato: ' + e.message) }
  }

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <h2 className="text-white font-bold">❓ Savollar ({questions.length})</h2>
        <div className="flex gap-2">
          <button onClick={() => { setShowCatForm(!showCatForm); setShowForm(false) }}
            className="bg-white/10 text-gray-300 px-3 py-1.5 rounded-xl text-xs font-semibold">
            📂 Kategoriya
          </button>
          <button onClick={() => { setShowForm(!showForm); setShowCatForm(false) }}
            className="btn-primary px-3 py-1.5 text-xs">
            {showForm ? '✕' : '➕ Savol'}
          </button>
        </div>
      </div>
      {msg && <div className={`card text-center text-sm ${msg.startsWith('✅') ? 'text-green-400' : 'text-red-400'}`}>{msg}</div>}

      {/* Kategoriya qo'shish formasi */}
      {showCatForm && (
        <form onSubmit={addCategory} className="card space-y-2 border border-blue-500/30">
          <p className="text-white font-bold text-sm">📂 Yangi kategoriya</p>
          <div className="flex gap-2">
            <input type="text" placeholder="Emoji (masalan: 🔢)" value={catForm.icon}
              onChange={e => setCatForm(f => ({ ...f, icon: e.target.value }))}
              className="w-16 p-2 rounded-xl bg-white/10 text-white border border-white/10 outline-none text-sm text-center"
              style={{ userSelect: 'text' }} />
            <input type="text" placeholder="Kategoriya nomi *" required value={catForm.name}
              onChange={e => setCatForm(f => ({ ...f, name: e.target.value }))}
              className="flex-1 p-2 rounded-xl bg-white/10 text-white border border-white/10 outline-none text-sm"
              style={{ userSelect: 'text' }} />
          </div>
          <button type="submit" className="btn-primary w-full py-2 text-sm">✅ Saqlash</button>
        </form>
      )}

      {/* Mavjud kategoriyalar */}
      {categories.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          {categories.map(c => (
            <span key={c.id} className="bg-blue-500/20 text-blue-300 text-xs px-2 py-1 rounded-full">
              {c.icon} {c.name}
            </span>
          ))}
        </div>
      )}
      {categories.length === 0 && (
        <div className="card bg-yellow-900/20 text-yellow-400 text-sm text-center py-2">
          ⚠️ Kategoriya yo'q — savollar "Barchasi" bo'limiga qo'shiladi
        </div>
      )}

      {showForm && (
        <form onSubmit={submit} className="card space-y-3">
          <textarea placeholder="Savol matni *" required rows={3} value={form.text}
            onChange={e => setForm(f => ({ ...f, text: e.target.value }))}
            className="w-full p-3 rounded-xl bg-white/10 text-white border border-white/10 outline-none resize-none text-sm" style={{ userSelect: 'text' }} />
          <div className="grid grid-cols-2 gap-2">
            <select value={form.difficulty} onChange={e => setForm(f => ({ ...f, difficulty: e.target.value }))}
              className="p-2 rounded-xl bg-white/10 text-white border border-white/10 outline-none text-sm">
              <option value="easy">🟢 Oson</option>
              <option value="medium">🟡 O'rta</option>
              <option value="hard">🔴 Qiyin</option>
            </select>
            <select value={form.category_id} onChange={e => setForm(f => ({ ...f, category_id: e.target.value }))}
              className="p-2 rounded-xl bg-white/10 text-white border border-white/10 outline-none text-sm">
              <option value="">Kategoriya</option>
              {categories.map(c => <option key={c.id} value={c.id}>{c.icon} {c.name}</option>)}
            </select>
          </div>
          <div className="space-y-2">
            <p className="text-gray-400 text-xs">Javob variantlari — to'g'risini tanlang:</p>
            {form.options.map((opt, idx) => (
              <div key={idx} className="flex gap-2 items-center">
                <button type="button" onClick={() => handleOption(idx, 'is_correct', true)}
                  className={`w-5 h-5 rounded-full border-2 flex-shrink-0 transition-all ${opt.is_correct ? 'bg-green-500 border-green-500' : 'border-gray-500'}`} />
                <input type="text" placeholder={`Variant ${idx + 1}`} required value={opt.text}
                  onChange={e => handleOption(idx, 'text', e.target.value)}
                  className="flex-1 p-2 rounded-lg bg-white/10 text-white border border-white/10 outline-none text-sm" style={{ userSelect: 'text' }} />
              </div>
            ))}
          </div>
          <input type="text" placeholder="Izoh (ixtiyoriy)" value={form.explanation}
            onChange={e => setForm(f => ({ ...f, explanation: e.target.value }))}
            className="w-full p-2 rounded-xl bg-white/10 text-white border border-white/10 outline-none text-sm" style={{ userSelect: 'text' }} />
          <button type="submit" className="btn-primary w-full">✅ Saqlash</button>
        </form>
      )}

      {loading ? <div className="text-center text-gray-400 py-4">Yuklanmoqda...</div> : (
        <div className="space-y-2">
          {questions.map(q => (
            <div key={q.id} className="card">
              <div className="flex justify-between items-start gap-2">
                <p className="text-white text-sm flex-1">{q.text.slice(0, 80)}{q.text.length > 80 ? '...' : ''}</p>
                <button onClick={() => deleteQ(q.id)} className="text-red-400 text-lg flex-shrink-0">🗑</button>
              </div>
              <div className="flex gap-2 mt-2 flex-wrap">
                <span className={`text-xs px-2 py-0.5 rounded-full ${q.difficulty === 'easy' ? 'bg-green-500/20 text-green-400' : q.difficulty === 'hard' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'}`}>{q.difficulty}</span>
                <span className="text-xs text-gray-500">So'ralgan: {q.times_asked}</span>
                <span className="text-xs text-gray-500">Aniqlik: {q.accuracy_rate}%</span>
              </div>
            </div>
          ))}
          {questions.length === 0 && <div className="card text-center text-gray-400 py-6">Hali savollar yo'q</div>}
        </div>
      )}
    </div>
  )
}
