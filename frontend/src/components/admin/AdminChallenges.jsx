import { useState, useEffect } from 'react'
import { api } from '../../services/api'

export default function AdminChallenges() {
  const [challenges, setChallenges] = useState([])
  const [selected, setSelected] = useState(null)
  const [participants, setParticipants] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [msg, setMsg] = useState('')
  const [addTgId, setAddTgId] = useState('')
  const [duration, setDuration] = useState(60)
  const [form, setForm] = useState({
    title: '', description: '', entry_fee: 0, min_prize_pool: 0,
    first_place_percent: 50, second_place_percent: 30,
    third_place_percent: 10, admin_commission: 10,
    total_questions: 20, time_per_question: 30,
    max_participants: 1000, difficulty: 'medium'
  })

  useEffect(() => { load() }, [])

  const load = async () => {
    try { setChallenges(await api.request('/api/admin/challenges')) }
    catch (e) { console.error(e) }
  }

  const loadParticipants = async (id) => {
    try {
      const data = await api.request(`/api/admin/challenges/${id}/participants`)
      setParticipants(data)
    } catch (e) { setMsg('Xato: ' + e.message) }
  }

  const totalPercent = +form.first_place_percent + +form.second_place_percent +
    +form.third_place_percent + +form.admin_commission

  const submit = async (e) => {
    e.preventDefault()
    if (Math.abs(totalPercent - 100) > 0.01) { setMsg(`Foizlar yig'indisi 100% bo'lishi kerak!`); return }
    try {
      await api.createChallenge(form)
      setMsg('✅ Challenge yaratildi!')
      setShowForm(false)
      load()
    } catch (e) {
      const errMsg = e?.message || (typeof e === 'object' ? JSON.stringify(e) : String(e))
      setMsg('❌ ' + errMsg)
    }
  }

  const startChallenge = async (id) => {
    try {
      const res = await api.request(`/api/admin/challenges/${id}/start`, {
        method: 'POST',
        body: JSON.stringify({ duration_minutes: duration })
      })
      setMsg(res.message)
      load()
      if (selected?.id === id) loadParticipants(id)
    } catch (e) { setMsg('Xato: ' + e.message) }
  }

  const finishChallenge = async (id) => {
    if (!confirm('Challengeni yakunlab g\'oliblarga pul berish?')) return
    try {
      const res = await api.request(`/api/admin/challenges/${id}/finish`, { method: 'POST' })
      setMsg(res.message)
      load()
      if (selected?.id === id) loadParticipants(id)
    } catch (e) { setMsg('Xato: ' + e.message) }
  }

  const addParticipant = async (challengeId) => {
    if (!addTgId) return
    try {
      const res = await api.addParticipant(challengeId, parseInt(addTgId))
      setMsg(res.message || '✅ Qo\'shildi')
      setAddTgId('')
      loadParticipants(challengeId)
      load()
    } catch (e) { setMsg('❌ ' + (e?.message || String(e))) }
  }

  // Challenge savollarini boshqarish
  const [challengeQuestions, setChallengeQuestions] = useState([])
  const [allQuestions, setAllQuestions] = useState([])
  const [showAddQ, setShowAddQ] = useState(false)

  const loadChallengeQuestions = async (ch) => {
    try {
      const allQ = await api.getQuestions({ page: 1, limit: 100 })
      setAllQuestions(Array.isArray(allQ) ? allQ : [])
      const ids = ch.question_ids || []
      setChallengeQuestions(ids)
    } catch (e) { console.error(e) }
  }

  const toggleQuestion = async (challengeId, questionId, currentIds) => {
    const newIds = currentIds.includes(questionId)
      ? currentIds.filter(id => id !== questionId)
      : [...currentIds, questionId]
    try {
      await api.request(`/api/admin/challenges/${challengeId}/questions`, {
        method: 'PUT',
        body: JSON.stringify({ question_ids: newIds })
      })
      setChallengeQuestions(newIds)
      setMsg(newIds.includes(questionId) ? '✅ Savol qo\'shildi' : '✅ Savol olib tashlandi')
    } catch (e) { setMsg('❌ ' + (e?.message || String(e))) }
  }

  const statusColor = (s) => ({
    active: 'bg-green-500/20 text-green-400',
    upcoming: 'bg-blue-500/20 text-blue-400',
    finished: 'bg-gray-500/20 text-gray-400',
    cancelled: 'bg-red-500/20 text-red-400',
  }[s] || 'bg-gray-500/20 text-gray-400')

  // Challenge detail view
  if (selected) {
    return (
      <div className="space-y-3">
        <button onClick={() => { setSelected(null); setParticipants([]); setChallengeQuestions([]); setAllQuestions([]) }} className="text-blue-400 text-sm">◀️ Orqaga</button>
        <div className="card">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="font-bold text-white text-lg">{selected.title}</h2>
              <span className={`text-xs px-2 py-0.5 rounded-full ${statusColor(selected.status)}`}>{selected.status}</span>
            </div>
            <div className="text-right text-sm">
              <div className="text-gray-400">Fond: <b className="text-white">{selected.prize_pool?.toLocaleString()} so'm</b></div>
              <div className="text-gray-400">Ishtirokchi: <b className="text-white">{selected.current_participants}/{selected.max_participants}</b></div>
            </div>
          </div>
          {selected.ends_at && (
            <div className="text-xs text-gray-400 mt-2">Tugash: {new Date(selected.ends_at).toLocaleString('uz-UZ')}</div>
          )}
        </div>

        {/* Boshqaruv */}
        <div className="card space-y-3">
          <h3 className="font-bold text-white text-sm">🎮 Boshqaruv</h3>
          {selected.status === 'upcoming' && (
            <div className="space-y-2">
              <div className="flex gap-2 items-center">
                <input type="number" value={duration} onChange={e => setDuration(+e.target.value)}
                  placeholder="Davomiyligi (daqiqa)" min="1" max="1440"
                  className="flex-1 p-2 rounded-xl bg-white/10 text-white border border-white/10 outline-none text-sm"
                  style={{ userSelect: 'text' }} />
                <button onClick={() => startChallenge(selected.id)}
                  className="btn-primary px-4 py-2 text-sm whitespace-nowrap">
                  ▶️ Boshlash
                </button>
              </div>
            </div>
          )}
          {selected.status === 'active' && (
            <button onClick={() => finishChallenge(selected.id)}
              className="w-full py-2 rounded-xl bg-red-500/20 text-red-400 text-sm font-bold">
              🏁 Yakunlash va G'oliblarga pul berish
            </button>
          )}
          {selected.winners_paid && (
            <div className="text-green-400 text-sm text-center">✅ G'oliblarga pul to'langan</div>
          )}
        </div>

        {/* Challengega Savollar qo'shish */}
        <div className="card space-y-2">
          <div className="flex justify-between items-center">
            <h3 className="font-bold text-white text-sm">❓ Challenge Savollari ({challengeQuestions.length})</h3>
            <button onClick={() => {
              setShowAddQ(!showAddQ)
              if (!showAddQ && allQuestions.length === 0) loadChallengeQuestions(selected)
            }} className="text-blue-400 text-xs">
              {showAddQ ? '▲ Yopish' : '➕ Savol qo\'shish'}
            </button>
          </div>
          {showAddQ && (
            <div className="space-y-1 max-h-48 overflow-y-auto">
              {allQuestions.length === 0 && (
                <p className="text-gray-400 text-xs text-center py-2">Hali savollar yo'q</p>
              )}
              {allQuestions.map(q => {
                const isAdded = challengeQuestions.includes(q.id)
                return (
                  <div key={q.id}
                    onClick={() => toggleQuestion(selected.id, q.id, challengeQuestions)}
                    className={`flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-all ${isAdded ? 'bg-green-500/20 border border-green-500/40' : 'bg-white/5 hover:bg-white/10'}`}>
                    <div className={`w-4 h-4 rounded-full flex-shrink-0 ${isAdded ? 'bg-green-500' : 'bg-gray-600'}`} />
                    <span className="text-white text-xs truncate">{q.text?.slice(0, 60)}</span>
                    <span className={`text-xs flex-shrink-0 px-1 rounded ${q.difficulty === 'easy' ? 'text-green-400' : q.difficulty === 'hard' ? 'text-red-400' : 'text-yellow-400'}`}>
                      {q.difficulty}
                    </span>
                  </div>
                )
              })}
            </div>
          )}
          {challengeQuestions.length > 0 && !showAddQ && (
            <p className="text-gray-400 text-xs">{challengeQuestions.length} ta savol tanlangan ✅</p>
          )}
        </div>

        {/* Ishtirokchi qo'shish */}
        {selected.status !== 'finished' && (
          <div className="card space-y-2">
            <h3 className="font-bold text-white text-sm">👤 Ishtirokchi qo'shish (Telegram ID)</h3>
            <div className="flex gap-2">
              <input type="number" placeholder="Telegram ID" value={addTgId}
                onChange={e => setAddTgId(e.target.value)}
                className="flex-1 p-2 rounded-xl bg-white/10 text-white border border-white/10 outline-none text-sm"
                style={{ userSelect: 'text' }} />
              <button onClick={() => addParticipant(selected.id)}
                className="btn-primary px-4 py-2 text-sm">
                ➕ Qo'shish
              </button>
            </div>
          </div>
        )}

        {msg && <div className="card text-center text-sm text-green-400">{msg}</div>}

        {/* Ishtirokchilar reytingi */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <h3 className="font-bold text-white text-sm">👥 Ishtirokchilar ({participants.length})</h3>
            <button onClick={() => loadParticipants(selected.id)} className="text-blue-400 text-xs">🔄</button>
          </div>
          {participants.length === 0 ? (
            <div className="card text-center text-gray-400 py-4">
              <button onClick={() => loadParticipants(selected.id)} className="text-blue-400 text-sm">
                Yuklab olish
              </button>
            </div>
          ) : participants.map((p, idx) => (
            <div key={p.user_id} className={`card flex items-center gap-3 ${idx < 3 ? 'border border-yellow-500/30' : ''}`}>
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold">
                {idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : idx + 1}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-white text-sm font-medium truncate">{p.full_name}</div>
                <div className="text-gray-400 text-xs">@{p.username || 'yo\'q'} · ID: {p.telegram_id}</div>
              </div>
              <div className="text-right text-xs">
                <div className="text-white font-bold">{p.score} ball</div>
                <div className="text-gray-400">{p.correct_answers} to'g'ri</div>
                {p.prize_earned > 0 && <div className="text-green-400">{p.prize_earned.toLocaleString()} so'm</div>}
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <h2 className="text-white font-bold">🏆 Challengelar</h2>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary px-4 py-2 text-sm">
          {showForm ? '✕' : '➕ Yaratish'}
        </button>
      </div>
      {msg && <div className="card text-center text-sm text-green-400">{msg}</div>}

      {showForm && (
        <form onSubmit={submit} className="card space-y-3">
          <input type="text" placeholder="Challenge nomi *" required value={form.title}
            onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
            className="w-full p-3 rounded-xl bg-white/10 text-white border border-white/10 outline-none text-sm"
            style={{ userSelect: 'text' }} />
          <textarea placeholder="Tavsif" value={form.description}
            onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
            rows={2} className="w-full p-2 rounded-xl bg-white/10 text-white border border-white/10 outline-none text-sm resize-none"
            style={{ userSelect: 'text' }} />
          <div className="grid grid-cols-2 gap-2">
            {[
              ['entry_fee', "Kirish to'lovi (so'm)"],
              ['min_prize_pool', 'Min. sovrin fondi'],
              ['total_questions', 'Savollar soni'],
              ['time_per_question', 'Vaqt/savol (s)'],
              ['max_participants', 'Max ishtirokchi'],
            ].map(([k, label]) => (
              <div key={k}>
                <label className="text-xs text-gray-400">{label}</label>
                <input type="number" value={form[k]} onChange={e => setForm(f => ({ ...f, [k]: +e.target.value }))}
                  className="w-full p-2 rounded-lg bg-white/10 text-white border border-white/10 outline-none text-sm mt-0.5"
                  style={{ userSelect: 'text' }} />
              </div>
            ))}
          </div>
          <div className="card bg-black/20 space-y-2">
            <p className="text-xs text-gray-300 font-bold">Taqsimlash % (jami=100%)</p>
            <div className="grid grid-cols-2 gap-2">
              {[
                ['first_place_percent', '🥇 1-o\'rin %'],
                ['second_place_percent', '🥈 2-o\'rin %'],
                ['third_place_percent', '🥉 3-o\'rin %'],
                ['admin_commission', '⚙️ Admin %'],
              ].map(([k, label]) => (
                <div key={k}>
                  <label className="text-xs text-gray-400">{label}</label>
                  <input type="number" min="0" max="100" step="0.1" value={form[k]}
                    onChange={e => setForm(f => ({ ...f, [k]: +e.target.value }))}
                    className="w-full p-2 rounded-lg bg-white/10 text-white border border-white/10 outline-none text-sm mt-0.5"
                    style={{ userSelect: 'text' }} />
                </div>
              ))}
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
          <div key={ch.id} onClick={() => { setSelected(ch); loadParticipants(ch.id) }}
            className="card cursor-pointer hover:bg-white/10 transition-all">
            <div className="flex justify-between items-start">
              <div>
                <div className="font-bold text-white">{ch.title}</div>
                <div className="text-xs text-gray-400 mt-0.5">
                  {ch.entry_fee > 0 ? `${ch.entry_fee.toLocaleString()} so'm` : 'Bepul'} ·
                  Fond: {ch.prize_pool.toLocaleString()} so'm
                </div>
              </div>
              <span className={`text-xs px-2 py-0.5 rounded-full flex-shrink-0 ${statusColor(ch.status)}`}>
                {ch.status}
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              👥 {ch.current_participants}/{ch.max_participants}
              {ch.ends_at && ` · ${new Date(ch.ends_at).toLocaleString('uz-UZ')}`}
              {ch.winners_paid && ' · ✅ To\'langan'}
            </div>
          </div>
        ))}
        {challenges.length === 0 && <div className="card text-center text-gray-400 py-6">Hali challengelar yo'q</div>}
      </div>
    </div>
  )
}
