import { useState, useEffect } from 'react'
import { api } from '../../services/api'

export default function AdminChallenges() {
  const [challenges, setChallenges] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [msg, setMsg] = useState('')
  const [form, setForm] = useState({
    title: '', description: '', entry_fee: 0, min_prize_pool: 0,
    first_place_percent: 50, second_place_percent: 30,
    third_place_percent: 10, admin_commission: 10,
    total_questions: 20, time_per_question: 30,
    max_participants: 1000, difficulty: 'medium'
  })

  useEffect(() => { load() }, [])

  const load = async () => {
    try {
      const data = await api.getChallenges(null, 1)
      setChallenges(data)
    } catch (e) { console.error(e) }
  }

  const totalPercent = +form.first_place_percent + +form.second_place_percent + +form.third_place_percent + +form.admin_commission

  const submit = async (e) => {
    e.preventDefault()
    if (Math.abs(totalPercent - 100) > 0.01) { setMsg(`Foizlar yig'indisi 100% bo'lishi kerak. Hozir: ${totalPercent}%`); return }
    try {
      await api.createChallenge(form)
      setMsg('✅ Challenge yaratildi!')
      setShowForm(false)
      load()
    } catch (e) { setMsg('Xato: ' + e.message) }
  }

  const field = (key, label, type = 'number') => (
    <div key={key}>
      <label className="text-xs text-gray-400">{label}</label>
      <input type={type} value={form[key]} onChange={e => setForm(f => ({ ...f, [key]: type === 'number' ? +e.target.value : e.target.value }))}
        className="w-full p-2 rounded-lg bg-white/10 text-white border border-white/10 outline-none text-sm mt-0.5" style={{ userSelect: 'text' }} />
    </div>
  )

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <h2 className="text-white font-bold">🏆 Challengelar</h2>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary px-4 py-2 text-sm">
          {showForm ? '✕ Yopish' : '➕ Yaratish'}
        </button>
      </div>
      {msg && <div className="card text-center text-sm text-green-400">{msg}</div>}

      {showForm && (
        <form onSubmit={submit} className="card space-y-3">
          {field('title', 'Nomi *', 'text')}
          <div>
            <label className="text-xs text-gray-400">Tavsif</label>
            <textarea value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              rows={2} className="w-full p-2 rounded-lg bg-white/10 text-white border border-white/10 outline-none text-sm mt-0.5 resize-none" style={{ userSelect: 'text' }} />
          </div>
          <div className="grid grid-cols-2 gap-2">
            {field('entry_fee', "Kirish to'lovi (so'm)")}
            {field('min_prize_pool', 'Min. sovrin fondi')}
            {field('total_questions', 'Savollar soni')}
            {field('time_per_question', 'Vaqt (soniya)')}
            {field('max_participants', 'Max ishtirokchi')}
          </div>
          <div className="card bg-black/20 space-y-2">
            <p className="text-xs text-gray-300 font-bold">Taqsimlash % (jami = 100%)</p>
            <div className="grid grid-cols-2 gap-2">
              {field('first_place_percent', '🥇 1-o\'rin %')}
              {field('second_place_percent', '🥈 2-o\'rin %')}
              {field('third_place_percent', '🥉 3-o\'rin %')}
              {field('admin_commission', '⚙️ Admin komissiya %')}
            </div>
            <div className={`text-sm font-bold text-center ${Math.abs(totalPercent - 100) < 0.01 ? 'text-green-400' : 'text-red-400'}`}>
              Jami: {totalPercent}% {Math.abs(totalPercent - 100) < 0.01 ? '✅' : '❌'}
            </div>
          </div>
          <button type="submit" className="btn-primary w-full">🏆 Challenge Yaratish</button>
        </form>
      )}

      <div className="space-y-2">
        {challenges.map(ch => (
          <div key={ch.id} className="card">
            <div className="flex justify-between items-start">
              <div>
                <div className="font-bold text-white">{ch.title}</div>
                <div className="text-xs text-gray-400 mt-0.5">
                  {ch.entry_fee > 0 ? `${ch.entry_fee.toLocaleString()} so'm` : 'Bepul'} · Fond: {ch.prize_pool.toLocaleString()} so'm
                </div>
              </div>
              <span className={`text-xs px-2 py-0.5 rounded-full flex-shrink-0 ${ch.status === 'active' ? 'bg-green-500/20 text-green-400' : ch.status === 'upcoming' ? 'bg-blue-500/20 text-blue-400' : 'bg-gray-500/20 text-gray-400'}`}>
                {ch.status}
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              👥 {ch.current_participants}/{ch.max_participants} · ❓ {ch.total_questions} ta savol
            </div>
          </div>
        ))}
        {challenges.length === 0 && <div className="card text-center text-gray-400 py-6">Hali challengelar yo'q</div>}
      </div>
    </div>
  )
}
