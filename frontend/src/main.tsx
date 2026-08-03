import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <div className="orb orb1" aria-hidden="true" />
    <div className="orb orb2" aria-hidden="true" />
    <App />
  </StrictMode>,
)
