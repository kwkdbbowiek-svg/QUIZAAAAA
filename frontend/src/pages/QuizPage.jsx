import { useState, useEffect, useCallback } from 'react'
import { api } from '../services/api'
import { useApp } from '../App'

export function QuizPage() {
  const { refreshUser } = useApp()
  const [phase, setPhase] = useState('menu') // menu | quiz | result
  const [categories, setCategories] = useState([])
  const [selectedCat, setSelectedCat] = useState(null)
  const [selectedDiff, setSelectedDiff] = useState(null)
  const [quizData, setQuizData] = useState(null)
  const [currentQ, setCurrentQ] = useState(null)
  const [answered, setAnswered] = useState(null)
  const [timer, setTimer] = useState(30)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.getCategories().then(setCategories).catch(() => {})
  }, [])

  // Timer countdown
  useEffect(() => {
    if (phase !== 'quiz' || answered !== null) return
    if (timer <= 0) {
      handleAnswer(-1) // Vaqt tugadi
      return
    }
    const t = setTimeout(() => setTimer(t => t - 1), 1000)
    return () => clearTimeout(t)
  }, [timer, phase, answered])

  const startQuiz = async () => {
    setLoading(true)
    try {
      const data = await api.startQuiz({
        ...(selectedCat && selectedCat !== 'all' ? { category_id: selectedCat } : {}),
        ...(selectedDiff && selectedDiff !== 'all' ? { difficulty: selectedDiff } : {}),
        count: 10,
      })
      setQuizData(data)
      setCurrentQ(data.question)
      setTimer(30)
      setAnswered(null)
      setPhase('quiz')
    } catch (err) {
      alert(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleAnswer = useCallback(async (optionIndex) => {
    if (answered !== null) return
    setAnswered(optionIndex)

    try {
      const res = await api.submitAnswer({
        question_id: currentQ.id,
        selected_option: optionIndex,
        time_taken: 30 - timer,
      })

      setAnswered({ index: optionIndex, is_correct: res.is_correct, correct_answer: res.correct_answer })

      setTimeout(() => {
        if (res.is_finished) {
          setResult(res)
          setPhase('result')
          refreshUser()
        } else {
          setCurrentQ(res.next_question)
          setTimer(30)
          setAnswered(null)
          setQuizData(prev => ({ ...prev, current: res.current, score: res.score }))
        }
      }, 1500)
    } catch (err) {
      console.error(err)
    }
  }, [answered, currentQ, timer])

  if (phase === 'menu') {
    return (
      <div className="p-4 max-w-md mx-auto space-y-4">
        <h1 className="text-xl font-bold text-white">🎯 Quiz Boshlash</h1>

        {/* Kategoriya */}
        <div className="card">
          <h3 className="font-semibold text-white mb-3">📚 Kategoriya</h3>
          <div className="grid grid-cols-2 gap-2">
            <button onClick={() => setSelectedCat('all')}
              className={`p-3 rounded-xl text-sm font-medium transition-all ${selectedCat === 'all' ? 'bg-blue-500 text-white' : 'bg-white/5 text-gray-300'}`}>
              🎲 Barchasi
            </button>
            {categories.map(cat => (
              <button key={cat.id} onClick={() => setSelectedCat(cat.id)}
                className={`p-3 rounded-xl text-sm font-medium transition-all ${selectedCat === cat.id ? 'bg-blue-500 text-white' : 'bg-white/5 text-gray-300'}`}>
                {cat.icon} {cat.name}
              </button>
            ))}
          </div>
        </div>

        {/* Qiyinlik */}
        <div className="card">
          <h3 className="font-semibold text-white mb-3">⚡ Qiyinlik darajasi</h3>
          <div className="flex gap-2">
            {[
              { id: 'all', label: '🎲 Aralash' },
              { id: 'easy', label: '🟢 Oson' },
              { id: 'medium', label: '🟡 O\'rta' },
              { id: 'hard', label: '🔴 Qiyin' },
            ].map(d => (
              <button key={d.id} onClick={() => setSelectedDiff(d.id)}
                className={`flex-1 p-2 rounded-xl text-xs font-medium transition-all ${selectedDiff === d.id ? 'bg-blue-500 text-white' : 'bg-white/5 text-gray-300'}`}>
                {d.label}
              </button>
            ))}
          </div>
        </div>

        <button onClick={startQuiz} disabled={loading || !selectedCat || !selectedDiff}
          className="btn-primary w-full disabled:opacity-50 text-lg py-4">
          {loading ? '⏳ Tayyorlanmoqda...' : '🚀 Boshlash'}
        </button>
      </div>
    )
  }

  if (phase === 'quiz' && currentQ) {
    const progress = quizData ? (quizData.current / quizData.total) * 100 : 0

    return (
      <div className="p-4 max-w-md mx-auto space-y-4">
        {/* Progress */}
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-400">Savol {quizData?.current}/{quizData?.total}</span>
          <span className="font-bold text-white">💯 {quizData?.score || 0}</span>
        </div>
        <div className="w-full h-2 bg-gray-700 rounded-full">
          <div className="progress-bar" style={{ width: `${progress}%` }} />
        </div>

        {/* Timer */}
        <div className="flex justify-center">
          <div className={`w-12 h-12 rounded-full border-4 flex items-center justify-center font-bold text-lg ${
            timer > 10 ? 'border-blue-500 text-blue-400' : 'border-red-500 text-red-400'
          }`}>
            {timer}
          </div>
        </div>

        {/* Question */}
        <div className="card">
          <p className="text-white text-lg font-medium leading-relaxed">{currentQ.text}</p>
        </div>

        {/* Options */}
        <div className="space-y-2">
          {currentQ.options.map((opt, idx) => {
            let cls = 'quiz-option'
            if (answered !== null) {
              const ansObj = typeof answered === 'object' ? answered : null
              if (ansObj) {
                if (opt.text === ansObj.correct_answer?.text) cls += ' correct'
                else if (idx === ansObj.index) cls += ' wrong'
                else cls += ' opacity-50'
              }
            }
            return (
              <button key={idx} onClick={() => handleAnswer(idx)}
                disabled={answered !== null}
                className={`${cls} w-full`}>
                <span className="font-bold mr-2 text-gray-400">{['A', 'B', 'C', 'D'][idx]}.</span>
                {opt.text}
              </button>
            )
          })}
        </div>
      </div>
    )
  }

  if (phase === 'result' && result) {
    const accuracy = Math.round((result.correct_count / quizData?.total) * 100)
    return (
      <div className="p-4 max-w-md mx-auto space-y-4 text-center">
        <div className="text-6xl">{accuracy >= 80 ? '🏆' : accuracy >= 50 ? '👍' : '📚'}</div>
        <h2 className="text-2xl font-bold text-white">Quiz Yakunlandi!</h2>
        <div className="card space-y-3">
          <Stat emoji="✅" label="To'g'ri javoblar" value={`${result.correct_count}/${quizData?.total}`} />
          <Stat emoji="💯" label="Ball" value={result.final_score} />
          <Stat emoji="🎯" label="Aniqlik" value={`${accuracy}%`} />
          <Stat emoji="⭐" label="Qozonilgan XP" value={`+${result.xp_earned || 0}`} />
        </div>
        <button onClick={() => setPhase('menu')} className="btn-primary w-full">🔄 Qaytadan</button>
      </div>
    )
  }

  return null
}

function Stat({ emoji, label, value }) {
  return (
    <div className="flex justify-between items-center py-1">
      <span className="text-gray-400">{emoji} {label}</span>
      <span className="font-bold text-white">{value}</span>
    </div>
  )
}
