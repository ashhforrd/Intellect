import { useEffect, useState, type FormEvent } from 'react'
import CollaborativeApp from './CollaborativeApp'
import { OwlMascot } from './OwlMascot'
import { authStore, useAuth } from './authStore'
import './login.css'

const LOGIN_HEADLINE = 'Turn team documents into shared understanding.'

export default function App() {
  const { user, ready, error } = useAuth()
  useEffect(() => { void authStore.load() }, [])
  if (!ready) return <div className="full-page-state"><OwlMascot size={28} /><span>Opening Intellect…</span></div>
  if (!user) return <LoginScreen externalError={error} />
  return <CollaborativeApp />
}

function LoginScreen({ externalError }: { externalError: string | null }) {
  const { loading, error } = useAuth()
  const [email, setEmail] = useState('atqiya@intellect.id')
  const [password, setPassword] = useState('IntellectDemo!2026')

  async function submit(event: FormEvent) {
    event.preventDefault()
    await authStore.login(email, password)
  }

  return <main className="login-page">
    <section className="login-context">
      <div className="login-brand"><span><OwlMascot size={27} /></span>intellect</div>
      <div><p>Project knowledge, kept in context</p><TypingHeadline /><span>Each project isolates its sources, conversations, knowledge graph, and next actions.</span></div>
      <small>Grounded answers · attributed prompts · project-level access</small>
    </section>
    <section className="login-panel">
      <form onSubmit={(event) => void submit(event)}>
        <div><h2>Sign in</h2><p>Use one of the seeded team accounts.</p></div>
        <label>Email<input type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} /></label>
        <label>Password<input type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
        {(error || externalError) && <p className="login-error">{error || externalError}</p>}
        <button type="submit" disabled={loading}>{loading ? 'Signing in…' : 'Sign in'}</button>
      </form>
    </section>
  </main>
}

function TypingHeadline() {
  const [length, setLength] = useState(0)

  useEffect(() => {
    let currentLength = 0
    const timer = window.setInterval(() => {
      currentLength += 1
      setLength(currentLength)
      if (currentLength >= LOGIN_HEADLINE.length) window.clearInterval(timer)
    }, 34)
    return () => window.clearInterval(timer)
  }, [])

  return <h1 className="typing-headline" aria-label={LOGIN_HEADLINE}>
    <span className="typing-headline-measure" aria-hidden="true">{LOGIN_HEADLINE}</span>
    <span className="typing-headline-text" aria-hidden="true">
      {LOGIN_HEADLINE.slice(0, length)}
      <i className={length >= LOGIN_HEADLINE.length ? 'complete' : ''} />
    </span>
  </h1>
}
