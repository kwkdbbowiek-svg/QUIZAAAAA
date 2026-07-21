import { useState, useEffect } from 'react'
import { useApp } from '../App'
import { api } from '../services/api'

export function AdminPage() {
  const { user } = useApp()
  const [activeTab, setActiveTab] = useState('stats')
  const [stats, setStats] = useState(null)
  const [channels, setChannels] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (activeTab === 'stats') loadStats()
    if (activeTab === 'channels') loadChannels()
  }, [activeTab])

  const loadStats = async () => {
    setLoading(true)
    try {
      const data = await api.getAdminStats()
      setStats(data)
    } finally {
      setLoading(false)
    }
  }

  const loadChannels = async () => {
    setLoading(true)
    try {
      const data = await api.getChannels()
      setChannels(data)
    } finally {
      setLoading(false)
    }
  }

  if (!user?.is_admin) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="card text-center">
          <div className="text-5xl mb-3">⛔</div>
          <p className="text-white">Admin huquqlari talab etiladi</p>
        </div>
      </div>
    )
  }

  const tabs = [
    { id: 'stats', label: '📊 Stat' },
    { id: 'channels', label: '📢 Kanallar' },
    { id: 'questions', label: '❓ Savollar' },
    { id: 'challenges', label: '🏆 Challenge' },
    { id: 'broadcast', label: '📣 Broadcast' },
  ]

  return (
    <div className="p-4 max-w-md mx-auto">
      <h1 className="text-xl font-bold text-white mb-4">⚙️ Admin Panel</h1>

      {/* Tab Navigation */}
      <div className="flex gap-2 overflow-x-auto pb-2 mb-4 no-scrollbar">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`whitespace-nowrap px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === tab.id ? 'bg-blue-500 text-white' : 'text-gray-400 bg-white/5'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'stats' && <StatsTab stats={stats} loading={loading} onRefresh={loadStats} />}
      {activeTab === 'channels' && <ChannelsTab channels={channels} onRefresh={loadChannels} />}
      {activeTab === 'questions' && <QuestionsTab />}
      {activeTab === 'challenges' && <ChallengesTab />}
      {activeTab === 'broadcast' && <BroadcastTab />}
    </div>
  )
}

function StatsTab({ stats, loading, onRefresh }) {
  if (loading) return <div className="text-center text-gray-400 py-8">Yuklanmoqda...</div>
  if (!stats) return null

  return (
    <div className="grid grid-cols-2 gap-3">
      {[
        { label: '👥 Jami users', value: stats.total_users },
        { label: '🆕 Bugun', value: stats.new_users_today },
        { label: '🟢 Kunlik faollar', value: stats.daily_active_users },
        { label: '🏆 Faol challengelar', value: stats.active_challenges },
        { label: '💰 Jami balans', value: `${stats.total_balance?.toLocaleString() || 0} so'm` },
        { label: '📈 Haftalik daromad', value: `${stats.weekly_income?.toLocaleString() || 0} so'm` },
      ].map(({ label, value }) => (
        <div key={label} className="card">
          <div className="text-xs text-gray-400">{label}</div>
          <div className="text-xl font-bold text-white mt-1">{value}</div>
        </div>
      ))}
      <button onClick={onRefresh} className="col-span-2 btn-secondary mt-2">🔄 Yangilash</button>
    </div>
  )
}

function ChannelsTab({ channels, onRefresh }) {
  const [showAdd, setShowAdd] = useState(false)
  const [form, setForm] = useState({ channel_id: '', channel_name: '', channel_link: '' })

  const handleAdd = async (e) => {
    e.preventDefault()
    try {
      await api.addChannel(form)
      setForm({ channel_id: '', channel_name: '', channel_link: '' })
      setShowAdd(false)
      onRefresh()
    } catch (err) {
      alert(err.message)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Kanalni o\'chirishni tasdiqlaysizmi?')) return
    await api.deleteChannel(id)
    onRefresh()
  }

  const handleToggle = async (id) => {
    await api.toggleChannel(id)
    onRefresh()
  }

  return (
    <div className="space-y-3">
      {channels.map(ch => (
        <div key={ch.id} className="card flex items-center justify-between">
          <div>
            <div className="font-medium text-white">{ch.channel_name}</div>
            <div className="text-xs text-gray-400">{ch.channel_id}</div>
          </div>
          <div className="flex gap-2">
            <button onClick={() => handleToggle(ch.id)}
              className={`px-2 py-1 rounded text-xs ${ch.is_active ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
              {ch.is_active ? '✅' : '❌'}
            </button>
            <button onClick={() => handleDelete(ch.id)}
              className="px-2 py-1 rounded text-xs bg-red-500/20 text-red-400">🗑</button>
          </div>
        </div>
      ))}

      <button onClick={() => setShowAdd(!showAdd)} className="btn-primary w-full">
        {showAdd ? '✕ Yopish' : '➕ Kanal qo\'shish'}
      </button>

      {showAdd && (
        <form onSubmit={handleAdd} className="card space-y-3">
          {[
            { key: 'channel_id', label: 'Kanal ID (@username yoki -100123...)', required: true },
            { key: 'channel_name', label: 'Kanal nomi', required: true },
            { key: 'channel_link', label: 'Kanal linki (ixtiyoriy)' },
          ].map(({ key, label, required }) => (
            <input key={key} type="text" placeholder={label} required={required}
              value={form[key]} onChange={e => setForm({ ...form, [key]: e.target.value })}
              className="w-full p-3 rounded-xl bg-white/10 text-white border border-white/10 focus:border-blue-500 outline-none"
              style={{ userSelect: 'text' }} />
          ))}
          <button type="submit" className="btn-primary w-full">✅ Saqlash</button>
        </form>
      )}
    </div>
  )
}

function QuestionsTab() {
  const [showForm, setShowForm] = useState(false)
  const [categories, setCategories] = useState([])
  const [form, setForm] = useState({
    text: '', difficulty: 'medium', category_id: '',
    options: [
      { text: '', is_correct: true },
      { text: '', is_correct: false },
      { text: '', is_correct: false },
      { text: '', is_correct: false },
    ],
    explanation: ''
  })

  useEffect(() => {
    api.getCategories().then(setCategories).catch(() => {})
  }, [])

  const handleOptionChange = (idx, field, value) => {
    const newOptions = form.options.map((opt, i) => {
      if (field === 'is_correct') {
        return { ...opt, is_correct: i === idx }
      }
      return i === idx ? { ...opt, [field]: value } : opt
    })
    setForm({ ...form, options: newOptions })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      await api.createQuestion({
        ...form,
        category_id: form.category_id ? parseInt(form.category_id) : null
      })
      alert('✅ Savol qo\'shildi!')
      setForm({
        text: '', difficulty: 'medium', category_id: '',
        options: [
          { text: '', is_correct: true },
          { text: '', is_correct: false },
          { text: '', is_correct: false },
          { text: '', is_correct: false },
        ],
        explanation: ''
      })
    } catch (err) {
      alert('Xato: ' + err.message)
    }
  }

  return (
    <div className="space-y-3">
      <button onClick={() => setShowForm(!showForm)} className="btn-primary w-full">
        {showForm ? '✕ Yopish' : '➕ Savol qo\'shish'}
      </button>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-3">
          <textarea
            placeholder="Savol matni *"
            required value={form.text}
            onChange={e => setForm({ ...form, text: e.target.value })}
            rows={3}
            className="w-full p-3 rounded-xl bg-white/10 text-white border border-white/10 focus:border-blue-500 outline-none resize-none"
            style={{ userSelect: 'text' }}
          />

          <div className="grid grid-cols-2 gap-2">
            <select value={form.difficulty} onChange={e => setForm({ ...form, difficulty: e.target.value })}
              className="p-3 rounded-xl bg-white/10 text-white border border-white/10 outline-none">
              <option value="easy">🟢 Oson</option>
              <option value="medium">🟡 O'rta</option>
              <option value="hard">🔴 Qiyin</option>
            </select>
            <select value={form.category_id} onChange={e => setForm({ ...form, category_id: e.target.value })}
              className="p-3 rounded-xl bg-white/10 text-white border border-white/10 outline-none">
              <option value="">Kategoriya</option>
              {categories.map(c => (
                <option key={c.id} value={c.id}>{c.icon} {c.name}</option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <p className="text-sm text-gray-400">Javob variantlari (to'g'risini belgilang):</p>
            {form.options.map((opt, idx) => (
              <div key={idx} className="flex gap-2 items-center">
                <button type="button"
                  onClick={() => handleOptionChange(idx, 'is_correct', true)}
                  className={`w-6 h-6 rounded-full border-2 flex-shrink-0 ${opt.is_correct ? 'bg-green-500 border-green-500' : 'border-gray-500'}`}
                />
                <input type="text" placeholder={`Variant ${idx + 1}`} required
                  value={opt.text} onChange={e => handleOptionChange(idx, 'text', e.target.value)}
                  className="flex-1 p-2 rounded-lg bg-white/10 text-white border border-white/10 outline-none text-sm"
                  style={{ userSelect: 'text' }} />
              </div>
            ))}
          </div>

          <input type="text" placeholder="Izoh (ixtiyoriy)"
            value={form.explanation} onChange={e => setForm({ ...form, explanation: e.target.value })}
            className="w-full p-3 rounded-xl bg-white/10 text-white border border-white/10 outline-none"
            style={{ userSelect: 'text' }} />

          <button type="submit" className="btn-primary w-full">✅ Saqlash</button>
        </form>
      )}
    </div>
  )
}

function ChallengesTab() {
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    title: '', description: '', entry_fee: 0, min_prize_pool: 0,
    first_place_percent: 50, second_place_percent: 30,
    third_place_percent: 10, admin_commission: 10,
    total_questions: 20, time_per_question: 30,
    max_participants: 1000, difficulty: 'medium'
  })

  const totalPercent = +form.first_place_percent + +form.second_place_percent +
    +form.third_place_percent + +form.admin_commission

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (Math.abs(totalPercent - 100) > 0.01) {
      alert(`Foizlar yig'indisi 100% bo'lishi kerak. Hozir: ${totalPercent}%`)
      return
    }
    try {
      await api.createChallenge(form)
      alert('✅ Challenge yaratildi!')
      setShowForm(false)
    } catch (err) {
      alert('Xato: ' + err.message)
    }
  }

  return (
    <div className="space-y-3">
      <button onClick={() => setShowForm(!showForm)} className="btn-primary w-full">
        {showForm ? '✕ Yopish' : '➕ Challenge yaratish'}
      </button>

      {showForm && (
        <form onSubmit={handleSubmit} className="card space-y-3">
          <input type="text" placeholder="Challenge nomi *" required
            value={form.title} onChange={e => setForm({ ...form, title: e.target.value })}
            className="w-full p-3 rounded-xl bg-white/10 text-white border border-white/10 outline-none"
            style={{ userSelect: 'text' }} />

          <textarea placeholder="Tavsif" value={form.description}
            onChange={e => setForm({ ...form, description: e.target.value })}
            rows={2} className="w-full p-3 rounded-xl bg-white/10 text-white border border-white/10 outline-none resize-none"
            style={{ userSelect: 'text' }} />

          <div className="grid grid-cols-2 gap-2">
            {[
              { key: 'entry_fee', label: 'Kirish to\'lovi (so\'m)' },
              { key: 'min_prize_pool', label: 'Min. sovrin fondi' },
              { key: 'total_questions', label: 'Savollar soni' },
              { key: 'time_per_question', label: 'Vaqt (soniya)' },
              { key: 'max_participants', label: 'Max ishtirokchi' },
            ].map(({ key, label }) => (
              <input key={key} type="number" placeholder={label}
                value={form[key]} onChange={e => setForm({ ...form, [key]: +e.target.value })}
                className="p-2 rounded-lg bg-white/10 text-white border border-white/10 outline-none text-sm"
                style={{ userSelect: 'text' }} />
            ))}
          </div>

          <div className="card bg-black/20">
            <p className="text-sm text-gray-300 mb-2">Taqsimlash foizlari (jami = 100%)</p>
            <div className="grid grid-cols-2 gap-2">
              {[
                { key: 'first_place_percent', label: '🥇 1-o\'rin %' },
                { key: 'second_place_percent', label: '🥈 2-o\'rin %' },
                { key: 'third_place_percent', label: '🥉 3-o\'rin %' },
                { key: 'admin_commission', label: '⚙️ Admin %' },
              ].map(({ key, label }) => (
                <div key={key}>
                  <label className="text-xs text-gray-400">{label}</label>
                  <input type="number" min="0" max="100" step="0.1"
                    value={form[key]} onChange={e => setForm({ ...form, [key]: +e.target.value })}
                    className="w-full p-2 rounded-lg bg-white/10 text-white border border-white/10 outline-none text-sm mt-1"
                    style={{ userSelect: 'text' }} />
                </div>
              ))}
            </div>
            <div className={`mt-2 text-sm font-bold ${Math.abs(totalPercent - 100) < 0.01 ? 'text-green-400' : 'text-red-400'}`}>
              Jami: {totalPercent}% {Math.abs(totalPercent - 100) < 0.01 ? '✅' : '❌'}
            </div>
          </div>

          <button type="submit" className="btn-primary w-full">🏆 Challenge Yaratish</button>
        </form>
      )}
    </div>
  )
}

function BroadcastTab() {
  const [form, setForm] = useState({ message_type: 'text', text: '', button_text: '', button_url: '' })
  const [sending, setSending] = useState(false)
  const [result, setResult] = useState(null)

  const handleSend = async (e) => {
    e.preventDefault()
    if (!confirm('Barcha foydalanuvchilarga xabar yuborishni tasdiqlaysizmi?')) return
    setSending(true)
    try {
      const data = await api.sendBroadcast(form)
      setResult(data)
    } catch (err) {
      alert('Xato: ' + err.message)
    } finally {
      setSending(false)
    }
  }

  return (
    <form onSubmit={handleSend} className="space-y-3">
      <select value={form.message_type} onChange={e => setForm({ ...form, message_type: e.target.value })}
        className="w-full p-3 rounded-xl bg-white/10 text-white border border-white/10 outline-none">
        <option value="text">📝 Matn</option>
        <option value="photo">🖼 Rasm</option>
        <option value="video">🎥 Video</option>
      </select>

      <textarea placeholder="Xabar matni *" required rows={5}
        value={form.text} onChange={e => setForm({ ...form, text: e.target.value })}
        className="w-full p-3 rounded-xl bg-white/10 text-white border border-white/10 outline-none resize-none"
        style={{ userSelect: 'text' }} />

      <input type="text" placeholder="Tugma matni (ixtiyoriy)"
        value={form.button_text} onChange={e => setForm({ ...form, button_text: e.target.value })}
        className="w-full p-3 rounded-xl bg-white/10 text-white border border-white/10 outline-none"
        style={{ userSelect: 'text' }} />

      <input type="url" placeholder="Tugma URL (ixtiyoriy)"
        value={form.button_url} onChange={e => setForm({ ...form, button_url: e.target.value })}
        className="w-full p-3 rounded-xl bg-white/10 text-white border border-white/10 outline-none"
        style={{ userSelect: 'text' }} />

      <button type="submit" disabled={sending} className="btn-primary w-full disabled:opacity-50">
        {sending ? '📤 Yuborilmoqda...' : '📣 Barcha Foydalanuvchilarga Yuborish'}
      </button>

      {result && (
        <div className="card text-green-400 text-center">
          ✅ Broadcast yaratildi! {result.total_recipients} ta foydalanuvchiga yuboriladi.
        </div>
      )}
    </form>
  )
}
