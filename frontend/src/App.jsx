import { useState, useEffect, createContext, useContext } from 'react'
import { ProfilePage } from './pages/ProfilePage'
import { QuizPage } from './pages/QuizPage'
import { ChallengePage } from './pages/ChallengePage'
import { LeaderboardPage } from './pages/LeaderboardPage'
import { AdminPage } from './pages/AdminPage'
import { BottomNav } from './components/BottomNav'
import { api } from './services/api'

// Global context
export const AppContext = createContext(null)
export const useApp = () => useContext(AppContext)

export default function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activePage, setActivePage] = useState('profile')
  const [error, setError] = useState(null)

  useEffect(() => {
    initApp()
  }, [])

  const initApp = async () => {
    try {
      const tg = window.Telegram?.WebApp
      
      if (!tg?.initData) {
        // Development mode
        console.warn('Telegram WebApp mavjud emas - development mode')
        setError('Bu sahifa Telegram orqali ochilishi kerak')
        setLoading(false)
        return
      }

      const response = await api.auth(tg.initData)
      setUser(response.user)
      
      // Admin sahifasiga yo'naltirish
      const urlParams = new URLSearchParams(window.location.search)
      if (urlParams.get('page') === 'admin' && response.user?.is_admin) {
        setActivePage('admin')
      }
    } catch (err) {
      setError('Kirish xatosi: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const refreshUser = async () => {
    try {
      const data = await api.getProfile()
      setUser(data)
    } catch (e) {
      console.error(e)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-white">Yuklanmoqda...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen p-4">
        <div className="card text-center">
          <div className="text-4xl mb-3">⚠️</div>
          <p className="text-white">{error}</p>
        </div>
      </div>
    )
  }

  const pages = {
    profile: <ProfilePage />,
    quiz: <QuizPage />,
    challenge: <ChallengePage />,
    leaderboard: <LeaderboardPage />,
    admin: <AdminPage />,
  }

  return (
    <AppContext.Provider value={{ user, setUser, refreshUser, activePage, setActivePage }}>
      <div className="min-h-screen pb-20">
        <div className="fade-in">
          {pages[activePage] || <ProfilePage />}
        </div>
        <BottomNav />
      </div>
    </AppContext.Provider>
  )
}
