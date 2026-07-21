import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { ChallengeQuizPage } from './ChallengeQuizPage'

export function ChallengePage() {
  const [challenges, setChallenges] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)
  const [quizMode, setQuizMode] = useState(null) // Challenge ID for quiz

  useEffect(() => {
    loadChallenges()
  }, [])

  const loadChallenges = async () => {
    setLoading(true)
    try {
      const data = await api.getChallenges()
      setChallenges(data)
    } finally {
      setLoading(false)
    }
  }

  const loadDetail = async (id) => {
    try {
      const data = await api.getChallenge(id)
      setSelected(data)
    } catch (err) {
      alert(err.message)
    }
  }

  const handleJoin = async (id) => {
    if (!confirm('Bu challengega qo\'shilishni tasdiqlaysizmi?')) return
    try {
      await api.joinChallenge(id)
      alert('✅ Muvaffaqiyatli qo\'shildingiz!')
      setSelected(null)
      loadChallenges()
    } catch (err) {
      alert('Xato: ' + err.message)
    }
  }

  // Quiz mode
  if (quizMode) {
    return <ChallengeQuizPage challengeId={quizMode} onBack={() => setQuizMode(null)} />
  }

  if (selected) {
    return <ChallengeDetail 
      challenge={selected} 
      onBack={() => setSelected(null)} 
      onJoin={handleJoin}
      onStartQuiz={(id) => setQuizMode(id)}
    />
  }

  return (
    <div className="p-4 max-w-md mx-auto space-y-4">
      <h1 className="text-xl font-bold text-white">🏆 Challenge'lar</h1>

      {loading && <p className="text-center text-gray-400 py-8">Yuklanmoqda...</p>}

      {!loading && challenges.length === 0 && (
        <div className="card text-center py-8">
          <div className="text-5xl mb-3">😔</div>
          <p className="text-gray-400">Hozircha faol challenge'lar mavjud emas</p>
        </div>
      )}

      <div className="space-y-3">
        {challenges.map(ch => (
          <div key={ch.id} onClick={() => loadDetail(ch.id)}
            className="card cursor-pointer hover:bg-white/10 transition-all">
            <div className="flex items-start justify-between mb-2">
              <h3 className="font-bold text-white text-lg">{ch.title}</h3>
              <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                ch.status === 'active' ? 'bg-green-500/20 text-green-400' : 'bg-blue-500/20 text-blue-400'
              }`}>
                {ch.status === 'active' ? '🟢 Faol' : '⏳ Kutilmoqda'}
              </span>
            </div>

            {ch.description && (
              <p className="text-sm text-gray-400 mb-3 line-clamp-2">{ch.description}</p>
            )}

            <div className="flex items-center justify-between text-sm">
              <div className="text-gray-300">
                💵 {ch.entry_fee > 0 ? `${ch.entry_fee.toLocaleString()} so'm` : '🎁 Bepul'}
              </div>
              <div className="text-yellow-400 font-bold">
                🏅 {ch.prize_pool.toLocaleString()} so'm
              </div>
            </div>

            <div className="flex items-center justify-between text-xs text-gray-500 mt-2 pt-2 border-t border-white/5">
              <span>❓ {ch.total_questions} ta savol</span>
              <span>👥 {ch.current_participants}/{ch.max_participants}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function ChallengeDetail({ challenge, onBack, onJoin, onStartQuiz }) {
  const [info, setInfo] = useState(null)
  
  useEffect(() => {
    loadInfo()
  }, [challenge.id])
  
  const loadInfo = async () => {
    try {
      const data = await api.request(`/api/challenge-quiz/${challenge.id}/info`)
      setInfo(data)
    } catch (err) {
      console.error(err)
    }
  }
  
  const prizeDist = [
    { place: '🥇 1-o\'rin', percent: challenge.first_place_percent, prize: challenge.prize_pool * challenge.first_place_percent / 100 },
    { place: '🥈 2-o\'rin', percent: challenge.second_place_percent, prize: challenge.prize_pool * challenge.second_place_percent / 100 },
    { place: '🥉 3-o\'rin', percent: challenge.third_place_percent, prize: challenge.prize_pool * challenge.third_place_percent / 100 },
  ]

  const canStartQuiz = info?.is_participant && info?.status === 'active' && !info?.finished

  return (
    <div className="p-4 max-w-md mx-auto space-y-4">
      <button onClick={onBack} className="text-blue-400 flex items-center gap-1">
        ◀️ Orqaga
      </button>

      <h1 className="text-2xl font-bold text-white">{challenge.title}</h1>

      {challenge.description && (
        <div className="card bg-gradient-to-br from-purple-900/30 to-blue-900/30">
          <p className="text-gray-300">{challenge.description}</p>
        </div>
      )}

      {/* User Status */}
      {info && (
        <div className={`card ${info.is_participant ? 'bg-green-900/20 border border-green-500/30' : 'bg-blue-900/20'}`}>
          {info.is_participant ? (
            <div>
              <div className="text-green-400 font-bold mb-2">✅ Siz ishtirokchisiz</div>
              {info.finished ? (
                <div className="text-white">
                  <div>🎯 Sizning ballingiz: <b>{info.my_score}</b></div>
                  {info.my_rank && <div>🏅 Reyting: <b>{info.my_rank}-o'rin</b></div>}
                  {info.my_prize > 0 && <div className="text-green-400">💰 Sovrin: <b>{info.my_prize.toLocaleString()} so'm</b></div>}
                </div>
              ) : info.status === 'active' ? (
                <div className="text-yellow-400">⚡ Challenge faol - test yechishingiz mumkin!</div>
              ) : (
                <div className="text-gray-400">⏳ Challenge boshlanishini kuting</div>
              )}
            </div>
          ) : (
            <div className="text-blue-400">ℹ️ Qo'shilish uchun pastdagi tugmani bosing</div>
          )}
        </div>
      )}

      {/* Main Stats */}
      <div className="grid grid-cols-2 gap-3">
        <div className="card bg-green-900/20 text-center">
          <div className="text-3xl mb-1">💵</div>
          <div className="text-lg font-bold text-white">
            {challenge.entry_fee > 0 ? `${challenge.entry_fee.toLocaleString()} so'm` : 'Bepul'}
          </div>
          <div className="text-xs text-gray-400">Kirish to'lovi</div>
        </div>
        <div className="card bg-yellow-900/20 text-center">
          <div className="text-3xl mb-1">🏅</div>
          <div className="text-lg font-bold text-white">{challenge.prize_pool.toLocaleString()} so'm</div>
          <div className="text-xs text-gray-400">Sovrin fondi</div>
        </div>
      </div>

      {/* Prize Distribution */}
      <div className="card">
        <h3 className="font-bold text-white mb-3">💰 G'oliblik taqsimoti</h3>
        {prizeDist.map(({ place, percent, prize }) => (
          <div key={place} className="flex justify-between items-center py-2 border-b border-white/5 last:border-0">
            <span className="text-gray-300">{place}</span>
            <div className="text-right">
              <div className="font-bold text-white">{prize.toLocaleString()} so'm</div>
              <div className="text-xs text-gray-400">{percent}%</div>
            </div>
          </div>
        ))}
      </div>

      {/* Details */}
      <div className="card space-y-2 text-sm">
        <InfoRow label="❓ Savollar soni" value={challenge.total_questions} />
        <InfoRow label="⏱ Har bir savol" value={`${challenge.time_per_question} soniya`} />
        <InfoRow label="👥 Ishtirokchilar" value={`${challenge.current_participants} / ${challenge.max_participants}`} />
        <InfoRow label="📊 Holat" value={
          challenge.status === 'active' ? '🟢 Faol' :
          challenge.status === 'upcoming' ? '⏳ Kutilmoqda' : challenge.status
        } />
        {challenge.starts_at && (
          <InfoRow label="🕐 Boshlanish" value={new Date(challenge.starts_at).toLocaleString('uz-UZ')} />
        )}
      </div>

      {/* Action Buttons */}
      {canStartQuiz ? (
        <button onClick={() => onStartQuiz(challenge.id)}
          className="btn-primary w-full text-lg py-4 glow animate-pulse">
          🎯 Testni Boshlash
        </button>
      ) : info?.is_participant ? (
        <div className="card text-center text-gray-400">
          {info.finished ? '✅ Siz allaqachon test yechdingiz' : '⏳ Challenge boshlanishini kuting'}
        </div>
      ) : (challenge.status === 'upcoming' || challenge.status === 'active') ? (
        <button onClick={() => onJoin(challenge.id)}
          className="btn-primary w-full text-lg py-4 glow">
          {challenge.entry_fee > 0 ? `💳 Qo'shilish (${challenge.entry_fee.toLocaleString()} so'm)` : '🎯 Tekin Qo\'shilish'}
        </button>
      ) : (
        <div className="card text-center text-gray-400">Challenge yakunlangan</div>
      )}
    </div>
  )
}

function InfoRow({ label, value }) {
  return (
    <div className="flex justify-between items-center py-1">
      <span className="text-gray-400">{label}</span>
      <span className="font-medium text-white">{value}</span>
    </div>
  )
}
