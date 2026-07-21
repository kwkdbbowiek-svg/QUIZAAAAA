import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

// Telegram Web App ni ishga tushirish
const tg = window.Telegram?.WebApp
if (tg) {
  tg.ready()
  tg.expand()
  tg.enableClosingConfirmation()
}

// Loading screeni yashirish
const loadingEl = document.getElementById('loading')
if (loadingEl) {
  setTimeout(() => {
    loadingEl.style.opacity = '0'
    loadingEl.style.transition = 'opacity 0.5s'
    setTimeout(() => loadingEl.remove(), 500)
  }, 500)
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
