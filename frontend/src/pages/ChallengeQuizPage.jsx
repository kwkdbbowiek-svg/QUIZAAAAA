import { useState, useEffect } from 'react'
import { api } from '../services/api'

export function ChallengeQuizPage({ challengeId, onBack }) {
  const [loading, setLoading] = useState(true)
  const [challenge, setChallenge] = useState(null)
  const [questions, setQuestions] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answers, setAnswers] = useState([])
  const [timeLeft, setTimeLeft] = useState(0)
  const [started, setStarted] = useState(false)
  const [finished, setFinished] = useState(false)
  const [result, setResult] = useState(null)
  const [leaderboard, setLeaderboard] = useState([])

  useEffect(() => {
    if (challengeId) loadChallengeInfo()
  }, [challengeId])

  useEffect(() => {
    if (started && timeLeft > 0) {
      const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000)
      return () => clearTimeout(timer)
    } else if (started && timeLeft === 0 && !finished) {
      handleTimeUp()
    }
  }, [timeLeft, started])

  const loadChallengeInfo = async () => {
    setLoading(true)
    try {
      const data = await api.request(`/api/challenge-quiz/${challengeId}/info`)
      setChallenge(data)
      
      if (data.finished) {
        setFinished(true)
        await loadLeaderboard()
      } else if (!data.is_participant) {
        alert('Siz bu challengega qo\'shilmagansiz!')
        onBack()
      } else if (data.status !== 'active') {
        alert('Challenge hali boshlanmagan yoki tugagan!')
        onBack()
      }
    } catch (err) {
      alert('Xato: ' + err.message)
      onBack()
    } finally {
      setLoading(false)
    }
  }

  const startQuiz = async () => {
    try {
      const data = await api.request(`/api/challenge-quiz/${challengeId}/start-quiz`)
      setQuestions(data.questions)
      setTimeLeft(data.time_per_question)
      setStarted(true)
      setAnswers([])
    } catch (err) {
      alert('Xato: ' + err.message)
    }
  }

  const selectAnswer = (optionIndex) => {
    if (finished) return
    
    const newAnswers = [...answers]
    newAnswers[currentIndex] = {
      question_id: questions[currentIndex].id,
      selected_option: optionIndex,
      time_taken: questions[currentIndex].time_limit - timeLeft
    }
    setAnswers(newAnswers)
  }

  const nextQuestion = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(currentIndex + 1)
      setTimeLeft(questions[currentIndex + 1].time_limit || 30)
    } else {
      submitAnswers()
    }
  }

  const handleTimeUp = () => {
    // Vaqt tugadi - javob bermasa, skip
    if (!answers[currentIndex]) {
      const newAnswers = [...answers]
      newAnswers[currentIndex] = {
        question_id: questions[currentIndex].id,
        selected_option: -1, // Javob bermagan
        time_taken: questions[currentIndex].time_limit || 30
      }
      setAnswers(newAnswers)
    }
    
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(currentIndex + 1)
      setTimeLeft(questions[currentIndex + 1].time_limit || 30)
    } else {
      submitAnswers()
    }
  }

  const submitAnswers = async () => {
    try {
      const data = await api.request(`/api/challenge-quiz/${challengeId}/submit`, {
        method: 'POST',
        body: JSON.stringify({ answers })
      })
      setResult(data)
      setFinished(true)
      await loadLeaderboard()
    } catch (err) {
      alert('Xato: ' + err.message)
    }
  }

  const loadLeaderboard = async () => {
    try {
      const data = await api.request(`/api/challenge-quiz/${challengeId}/leaderboard`)
      setLeaderboard(data.leaderboard || [])
    } catch (err) {
      console.error('Leaderboard xatosi:', err)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-gray-900 to-black">
        <div className="text-center">
          <div className="text-6xl mb-4 animate-bounce">⏳</div>
          <p className="text-white text-lg">Yuklanmoqda...</p>
        </div>
      </div>
    )
  }

  if (finished) {
    return (
      <div className="p-4 max-w-2xl mx-auto space-y-4">
        <h1 className="text-2xl font-bold text-white text-center">🏆 Challenge Yakunlandi!</h1>
        
        {result && (
          <div className="card bg-gradient-to-br from-purple-900/30 to-blue-900/30 text-center">
            <div className="text-5xl mb-3">🎯</div>
            <div className="text-3xl font-bold text-white mb-2">{result.score} ball</div>
            <div className="text-gray-300">
              {result.correct} / {result.total} to'g'ri javob
            </div>
            <div className="text-sm text-gray-400 mt-2">
              Vaqt: {result.time_spent?.toFixed(1)}s
            </div>
            {result.message && (
              <div className="mt-3 text-yellow-400 text-sm">{result.message}</div>
            )}
          </div>
        )}

        {/* Leaderboard */}
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h2 className="font-bold text-white text-lg">📊 Reyting</h2>
            <button onClick={loadLeaderboard} className="text-blue-400 text-sm">🔄 Yangilash</button>
          </div>
          
          {leaderboard.length === 0 && (
            <p className="text-center text-gray-400 py-4">Ma'lumot yuklanmoqda...</p>
          )}
          
          <div className="space-y-2">
            {leaderboard.map((entry, idx) => (
              <div key={idx} className={`flex items-center gap-3 p-3 rounded-xl ${
                entry.is_me ? 'bg-blue-500/20 border border-blue-500/40' : 'bg-white/5'
              }`}>
                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg ${
                  entry.rank === 1 ? 'bg-yellow-500 text-black' :
                  entry.rank === 2 ? 'bg-gray-300 text-black' :
                  entry.rank === 3 ? 'bg-orange-600 text-white' :
                  'bg-gray-700 text-white'
                }`}>
                  {entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : entry.rank === 3 ? '🥉' : entry.rank}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-white truncate">
                    {entry.full_name} {entry.is_me && '(Siz)'}
                  </div>
                  <div className="text-xs text-gray-400">
                    @{entry.username || 'yo\'q'} · {entry.correct_answers} to'g'ri · {entry.time_spent}s
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="font-bold text-white">{entry.score}</div>
                  {entry.prize_earned > 0 && (
                    <div className="text-xs text-green-400">{entry.prize_earned.toLocaleString()} so'm</div>
                  )}
                  {!entry.finished && (
                    <div className="text-xs text-yellow-400">⏳</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        <button onClick={onBack}
          className="btn-primary w-full">
          ◀️ Challengelarga qaytish
        </button>
      </div>
    )
  }

  if (!started) {
    return (
      <div className="p-4 max-w-md mx-auto space-y-4">
        <h1 className="text-2xl font-bold text-white text-center">{challenge?.title}</h1>
        
        <div className="card bg-gradient-to-br from-purple-900/30 to-blue-900/30 text-center py-8">
          <div className="text-6xl mb-4">🎯</div>
          <h2 className="text-xl font-bold text-white mb-2">Tayyor bo'lishingizni tekshiring!</h2>
          <p className="text-gray-300 mb-4">
            Siz {challenge?.total_questions} ta savolga javob berasiz
          </p>
          <div className="text-sm text-gray-400 space-y-1">
            <div>⏱ Har bir savol: {challenge?.time_per_question}s</div>
            <div>🏅 Sovrin fondi: {challenge?.prize_pool?.toLocaleString()} so'm</div>
            <div>👥 Ishtirokchilar: {challenge?.current_participants}</div>
          </div>
        </div>

        <button onClick={startQuiz}
          className="btn-primary w-full text-lg py-4 glow">
          🚀 Boshlash
        </button>
        
        <button onClick={onBack}
          className="w-full py-3 text-gray-400">
          ◀️ Bekor qilish
        </button>
      </div>
    )
  }

  const currentQuestion = questions[currentIndex]
  const currentAnswer = answers[currentIndex]

  return (
    <div className="p-4 max-w-2xl mx-auto space-y-4">
      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm text-gray-300">
          <span>Savol {currentIndex + 1} / {questions.length}</span>
          <span className={`font-bold ${timeLeft <= 5 ? 'text-red-400 animate-pulse' : 'text-yellow-400'}`}>
            ⏱ {timeLeft}s
          </span>
        </div>
        <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
          <div className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-300"
            style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }} />
        </div>
      </div>

      {/* Question */}
      <div className="card bg-gradient-to-br from-indigo-900/30 to-purple-900/30">
        <div className="text-lg font-medium text-white mb-4">
          {currentQuestion?.text}
        </div>
        
        {currentQuestion?.media_file_id && (
          <div className="mb-4 text-center text-gray-400">
            📷 Media: {currentQuestion.media_file_id}
          </div>
        )}

        {/* Options */}
        <div className="space-y-2">
          {currentQuestion?.options?.map((opt) => (
            <button
              key={opt.index}
              onClick={() => selectAnswer(opt.index)}
              className={`w-full p-4 rounded-xl text-left transition-all ${
                currentAnswer?.selected_option === opt.index
                  ? 'bg-blue-500 text-white shadow-lg scale-105'
                  : 'bg-white/10 text-gray-300 hover:bg-white/20'
              }`}
            >
              <div className="flex items-center gap-3">
                <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                  currentAnswer?.selected_option === opt.index
                    ? 'border-white bg-white'
                    : 'border-gray-500'
                }`}>
                  {currentAnswer?.selected_option === opt.index && (
                    <div className="w-3 h-3 rounded-full bg-blue-500" />
                  )}
                </div>
                <span className="flex-1">{opt.text}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Next Button */}
      <button
        onClick={nextQuestion}
        disabled={currentAnswer === undefined}
        className={`btn-primary w-full text-lg py-4 ${
          currentAnswer === undefined ? 'opacity-50 cursor-not-allowed' : 'glow'
        }`}
      >
        {currentIndex < questions.length - 1 ? '➡️ Keyingi savol' : '🏁 Yakunlash'}
      </button>
    </div>
  )
}
