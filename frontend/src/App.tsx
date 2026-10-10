import { useEffect, useState, type FormEvent } from 'react'
import CollaborativeApp from './CollaborativeApp'
import { OwlMascot } from './OwlMascot'
import { authStore, useAuth } from './authStore'
import './login.css'

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
      <div><p>PROJECT KNOWLEDGE, KEPT IN CONTEXT</p><h1>Turn team documents into shared understanding.</h1><span>Each project isolates its sources, conversations, knowledge graph, and next actions.</span></div>
      <small>Grounded answers · attributed prompts · project-level access</small>
    </section>
    <section className="login-panel">
      <form onSubmit={(event) => void submit(event)}>
        <div><h2>Sign in</h2><p>Use one of the seeded team accounts.</p></div>
        <label>Email<input type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} /></label>
        <label>Password<input type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
        {(error || externalError) && <p className="login-error">{error || externalError}</p>}
        <button type="submit" disabled={loading}>{loading ? 'Signing in…' : 'Sign in'}</button>
        <div className="demo-accounts"><span>Demo accounts</span>{['lucas@intellect.id', 'kezia@intellect.id', 'atqiya@intellect.id'].map((account) => <button type="button" key={account} onClick={() => setEmail(account)}>{account}</button>)}</div>
      </form>
    </section>
  </main>
}
