/**
 * API Service — barcha API so'rovlar shu orqali o'tadi
 */

class ApiService {
  constructor() {
    this.token = localStorage.getItem('eduquiz_token') || null
  }

  setToken(token) {
    this.token = token
    if (token) localStorage.setItem('eduquiz_token', token)
    else localStorage.removeItem('eduquiz_token')
  }

  async request(endpoint, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...options.headers }
    if (this.token) headers['Authorization'] = `Bearer ${this.token}`

    let url = endpoint.startsWith('http') ? endpoint : endpoint
    const res = await fetch(url, { ...options, headers })

    if (!res.ok) {
      let msg = `HTTP ${res.status}`
      try { const d = await res.json(); msg = d.detail || d.message || msg } catch {}
      throw new Error(msg)
    }
    return res.json()
  }

  // ─── Auth ──────────────────────────────────────────────────────────────────
  async auth(initData) {
    const data = await this.request('/api/auth/telegram', {
      method: 'POST',
      body: JSON.stringify({ init_data: initData }),
    })
    this.setToken(data.access_token)
    return data
  }

  async adminLogin(username, password) {
    const data = await this.request('/api/auth/admin-login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    })
    this.setToken(data.access_token)
    return data
  }

  // ─── User ──────────────────────────────────────────────────────────────────
  async getProfile() {
    return this.request('/api/users/me')
  }

  async getTransactions(page = 1) {
    return this.request(`/api/users/me/transactions?page=${page}&limit=20`)
  }

  async getLeaderboard(type = 'global', limit = 50) {
    return this.request(`/api/users/leaderboard/${type}?limit=${limit}`)
  }

  // ─── Quiz ──────────────────────────────────────────────────────────────────
  async getCategories() {
    return this.request('/api/categories')
  }

  async startQuiz(params) {
    const q = new URLSearchParams(params).toString()
    return this.request(`/api/quiz/start?${q}`)
  }

  async submitAnswer(data) {
    return this.request('/api/quiz/answer', { method: 'POST', body: JSON.stringify(data) })
  }

  // ─── Challenges ────────────────────────────────────────────────────────────
  async getChallenges(status = null, page = 1) {
    const q = new URLSearchParams({ page, limit: 10 })
    if (status) q.set('status', status)
    return this.request(`/api/challenges?${q}`)
  }

  async getChallenge(id) {
    return this.request(`/api/challenges/${id}`)
  }

  async joinChallenge(id) {
    return this.request(`/api/challenges/${id}/join`, { method: 'POST' })
  }

  // ─── Admin ─────────────────────────────────────────────────────────────────
  async getAdminStats() {
    return this.request('/api/admin/stats')
  }

  async searchUsers(query, page = 1) {
    return this.request(`/api/admin/users/search?q=${encodeURIComponent(query)}&page=${page}&limit=20`)
  }

  async adjustBalance(userId, amount, operation, note) {
    return this.request(`/api/admin/users/${userId}/balance`, {
      method: 'PATCH',
      body: JSON.stringify({ amount, operation, note }),
    })
  }

  async getChannels() {
    return this.request('/api/admin/channels')
  }

  async addChannel(data) {
    return this.request('/api/admin/channels', { method: 'POST', body: JSON.stringify(data) })
  }

  async deleteChannel(id) {
    return this.request(`/api/admin/channels/${id}`, { method: 'DELETE' })
  }

  async toggleChannel(id) {
    return this.request(`/api/admin/channels/${id}/toggle`, { method: 'PATCH' })
  }

  async createQuestion(data) {
    return this.request('/api/admin/questions', { method: 'POST', body: JSON.stringify(data) })
  }

  async getQuestions(params = {}) {
    const q = new URLSearchParams(params).toString()
    return this.request(`/api/questions?${q}`)
  }

  async deleteQuestion(id) {
    return this.request(`/api/admin/questions/${id}`, { method: 'DELETE' })
  }

  async createChallenge(data) {
    return this.request('/api/admin/challenges', { method: 'POST', body: JSON.stringify(data) })
  }

  async sendBroadcast(data) {
    return this.request('/api/admin/broadcasts/send', { method: 'POST', body: JSON.stringify(data) })
  }

  async adminGetChallenges() {
    return this.request('/api/admin/challenges')
  }

  async startChallenge(id, durationMinutes) {
    return this.request(`/api/admin/challenges/${id}/start`, {
      method: 'POST',
      body: JSON.stringify({ duration_minutes: durationMinutes }),
    })
  }

  async finishChallenge(id) {
    return this.request(`/api/admin/challenges/${id}/finish`, { method: 'POST' })
  }

  async addParticipant(challengeId, telegramId) {
    return this.request(`/api/admin/challenges/${challengeId}/add-participant`, {
      method: 'POST',
      body: JSON.stringify({ telegram_id: telegramId }),
    })
  }

  async getParticipants(challengeId) {
    return this.request(`/api/admin/challenges/${challengeId}/participants`)
  }

  async getBroadcasts() {
    return this.request('/api/admin/broadcasts')
  }
}

export const api = new ApiService()
