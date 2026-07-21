/**
 * API Service - Backend bilan aloqa
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class ApiService {
  constructor() {
    this.token = localStorage.getItem('token')
  }

  async request(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Xato' }))
      throw new Error(error.detail || 'Server xatosi')
    }

    return response.json()
  }

  // ─── Auth ─────────────────────────────────────────────────────────────────
  async auth(initData) {
    const data = await this.request('/api/auth/telegram', {
      method: 'POST',
      body: JSON.stringify({ init_data: initData }),
    })
    this.token = data.access_token
    localStorage.setItem('token', this.token)
    return data
  }

  // ─── User ─────────────────────────────────────────────────────────────────
  async getProfile() {
    return this.request('/api/users/me')
  }

  async getTransactions(page = 1) {
    return this.request(`/api/users/me/transactions?page=${page}&limit=20`)
  }

  async getLeaderboard(type = 'global', limit = 50) {
    return this.request(`/api/users/leaderboard/${type}?limit=${limit}`)
  }

  // ─── Quiz ─────────────────────────────────────────────────────────────────
  async getCategories() {
    return this.request('/api/categories')
  }

  async startQuiz(params) {
    const query = new URLSearchParams(params).toString()
    return this.request(`/api/quiz/start?${query}`)
  }

  async submitAnswer(data) {
    return this.request('/api/quiz/answer', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // ─── Challenges ───────────────────────────────────────────────────────────
  async getChallenges(status = null, page = 1) {
    const query = new URLSearchParams({ page, limit: 10 })
    if (status) query.set('status', status)
    return this.request(`/api/challenges?${query}`)
  }

  async getChallenge(id) {
    return this.request(`/api/challenges/${id}`)
  }

  async joinChallenge(id) {
    return this.request(`/api/challenges/${id}/join`, { method: 'POST' })
  }

  // ─── Admin ────────────────────────────────────────────────────────────────
  async getAdminStats() {
    return this.request('/api/admin/stats')
  }

  async searchUsers(query, page = 1) {
    return this.request(`/api/admin/search?q=${query}&page=${page}&limit=20`)
  }

  async adjustBalance(userId, amount, operation, note) {
    return this.request(`/api/admin/${userId}/balance`, {
      method: 'PATCH',
      body: JSON.stringify({ amount, operation, note }),
    })
  }

  async getChannels() {
    return this.request('/api/admin/channels')
  }

  async addChannel(data) {
    return this.request('/api/admin/channels', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async deleteChannel(id) {
    return this.request(`/api/admin/channels/${id}`, { method: 'DELETE' })
  }

  async toggleChannel(id) {
    return this.request(`/api/admin/channels/${id}/toggle`, { method: 'PATCH' })
  }

  async createQuestion(data) {
    return this.request('/api/admin/questions', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getQuestions(params) {
    const query = new URLSearchParams(params).toString()
    return this.request(`/api/questions?${query}`)
  }

  async createChallenge(data) {
    return this.request('/api/admin/challenges', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async sendBroadcast(data) {
    return this.request('/api/admin/broadcasts/send', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }
}

export const api = new ApiService()
