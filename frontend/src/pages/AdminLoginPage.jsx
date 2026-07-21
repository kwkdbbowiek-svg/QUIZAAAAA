import { useState } from 'react'
import { api } from '../services/api'

export function AdminLoginPage({ onLogin }) {
  const [form, setForm] = useState({ username: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const res = await fetch('/api/auth/admin-login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: form.username, password: form.password })
      })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || `Server xatosi: ${res.status}`)
      }
      // Tokenni saqlash
      localStorage.setItem('token', data.access_token)
      onLogin(data.user)
    } catch (err) {
      if (err.message === 'Failed to fetch') {
        setError('Server bilan aloqa yo\'q. Sahifani yangilang.')
      } else {
        setError(err.message || 'Login yoki parol noto\'g\'ri')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex items-center justify-center min-h-screen p-6">
      <div className="card max-w-sm w-full space-y-6">
        <div className="text-center">
          <div className="text-5xl mb-2">⚙️</div>
          <h1 className="text-xl font-bold text-white">Admin Panel</h1>
          <p className="text-gray-400 text-sm">EduQuiz Platform</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-gray-400 text-xs mb-1 block">Login</label>
            <input
              type="text"
              placeholder="admin"
              value={form.username}
              onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
              required
              className="w-full p-3 rounded-xl bg-white/10 text-white border border-white/10 focus:border-blue-500 outline-none"
              style={{ userSelect: 'text' }}
            />
          </div>
          <div>
            <label className="text-gray-400 text-xs mb-1 block">Parol</label>
            <input
              type="password"
              placeholder="••••••••"
              value={form.password}
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              required
              className="w-full p-3 rounded-xl bg-white/10 text-white border border-white/10 focus:border-blue-500 outline-none"
              style={{ userSelect: 'text' }}
            />
          </div>

          {error && (
            <div className="text-red-400 text-sm text-center bg-red-500/10 p-2 rounded-xl">
              ❌ {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full py-3 text-base font-bold disabled:opacity-50"
          >
            {loading ? '⏳ Kirish...' : '🔑 Kirish'}
          </button>
        </form>
      </div>
    </div>
  )
}
