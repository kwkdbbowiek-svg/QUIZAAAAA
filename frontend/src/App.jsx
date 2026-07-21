import { useState, useEffect, createContext, useContext } from 'react'
import { ProfilePage } from './pages/ProfilePage'
import { QuizPage } from './pages/QuizPage'
import { ChallengePage } from './pages/ChallengePage'
import { LeaderboardPage } from './pages/LeaderboardPage'
import { AdminPage } from './pages/AdminPage'
import { AdminLoginPage } from './pages/AdminLoginPage'
import { BottomNav } from './components/BottomNav'
import { api } from './services/api'

export const AppContext = createContext(null)
export const useApp = () => useContext(AppContext)

export default function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activePage, setActivePage] = useState('profile')
  const [isBrowser, setIsBrowser] = useState(false)
  const [showAdminLogin, setShowAdminLogin] = useState(false)

  useEffect(() => { initApp() }, [])

  const initApp = async () => {
    const tg = window.Telegram?.WebApp
    const isAdminPath = window.location.pathname.startsWith('/admin')

    if (!tg?.initData) {
      // Brauzerda ochilgan
      setIsBrowser(true)
      const savedToken = api.token
      if (savedToken) {
        try {
          const data = await api.getProfile()
          setUser({ ...data, is_admin: data.is_admin || false })
          setActivePage(isAdminPath || data.is_admin ? 'admin' : 'profile')
        } catch {
          api.setToken(null)
          if (isAdminPath) setShowAdminLogin(true)
        }
      } else if (isAdminPath) {
        setShowAdminLogin(true)
      }
      setLoading(false)
      return
    }

    // Telegram WebApp
    try {
      tg.ready()
      tg.expand()
      const response = await api.auth(tg.initData)
      const userData = response.user
      setUser(userData)
      // Admin bo'lsa admin panelga, aks holda profil
      setActivePage(userData?.is_admin ? 'admin' : 'profile')
    } catch (err) {
      console.error('Auth xatosi:', err.message)
    } finally {
      setLoading(false)
    }
  }

  const refreshUser = async () => {
    try {
      const data = await api.getProfile()
      setUser(prev => ({ ...prev, ...data }))
    } catch (e) { console.error(e) }
  }

  if (loading) return (
    <div className="flex items-center justify-center h-screen">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-white text-sm">Yuklanmoqda...</p>
      </div>
    </div>
  )

  // Admin login (brauzerda)
  if (showAdminLogin && !user) {
    return (
      <AdminLoginPage onLogin={(u) => {
        setUser(u)
        setShowAdminLogin(false)
        setActivePage('admin')
      }} />
    )
  }

  // Brauzerda, login qilinmagan
  if (isBrowser && !user) {
    return (
      <div className="flex items-center justify-center h-screen p-6">
        <div className="card text-center space-y-4 max-w-sm w-full">
          <div className="text-6xl">🎓</div>
          <h1 className="text-2xl font-bold text-white">EduQuiz Platform</h1>
          <p className="text-gray-400 text-sm">Bu platforma Telegram Mini App sifatida ishlaydi.</p>
          <div className="card bg-blue-900/30 text-left space-y-2">
            <p className="text-white text-sm font-bold">Ishlatish uchun:</p>
            <p className="text-gray-300 text-sm">1. Telegram'da <b>@portal112bot</b> ni oching</p>
            <p className="text-gray-300 text-sm">2. <b>/start</b> yuboring</p>
            <p className="text-gray-300 text-sm">3. <b>👤 Profilim</b> → Web panel</p>
          </div>
          <a href="https://t.me/portal112bot" className="btn-primary w-full block text-center py-3">
            📱 Botga o'tish
          </a>
          <button onClick={() => setShowAdminLogin(true)}
            className="text-gray-500 text-xs hover:text-gray-300 transition-colors">
            ⚙️ Admin Panel
          </button>
        </div>
      </div>
    )
  }

  const pages = {
    profile:     <ProfilePage />,
    quiz:        <QuizPage />,
    challenge:   <ChallengePage />,
    leaderboard: <LeaderboardPage />,
    admin:       <AdminPage />,
  }

  return (
    <AppContext.Provider value={{ user, setUser, refreshUser, activePage, setActivePage }}>
      <div className="min-h-screen pb-20">
        <div className="fade-in">{pages[activePage] || <ProfilePage />}</div>
        <BottomNav />
      </div>
    </AppContext.Provider>
  )
}
