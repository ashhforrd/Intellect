import { LoginField } from './components/LoginField'
import { FullPageState } from './components/FullPageState'
import { useEffect, useState, type FormEvent } from 'react'
import CollaborativeApp from './CollaborativeApp'
import { OwlMascot } from './OwlMascot'
import { authStore, useAuth } from './authStore'
const LOGIN_HEADLINE = 'Turn team documents into shared understanding.'
export default function App() {
  const { user, ready, error } = useAuth()
  useEffect(() => { void authStore.load() }, [])
  if (!ready)
    return <FullPageState label="Opening Intellect…" />
  if (!user)
    return <LoginScreen externalError={error} />
  return <CollaborativeApp />
}
function LoginScreen({ externalError }: {
  externalError: string | null
}) {
  const { loading, error } = useAuth()
  const [email, setEmail] = useState('atqiya@intellect.id')
  const [password, setPassword] = useState('IntellectDemo!2026')
  async function submit(event: FormEvent) {
    event.preventDefault()
    await authStore.login(email, password)
  }
  return <main
    className="grid h-screen min-h-screen min-w-0 [grid-template-columns:minmax(0,_1.15fr)_minmax(26.25rem,_.85fr)] bg-neutral-950 text-neutral-100 login-compact:block"
  >
    <section className="flex min-h-screen flex-col justify-between bg-neutral-950 login-surface px-13.5 py-10.5 login-compact:hidden">
      <div className="flex items-center gap-2.75 font-mono text-lg font-bold"><span className="grid size-10.5 place-items-center rounded-xl bg-neutral-100 text-neutral-900">
        <OwlMascot size={27} />
      </span>intellect</div>
      <div className="max-w-170">
        <p className="mt-0 mb-5 text-xs font-bold tracking-eyebrow text-neutral-500">Project knowledge, kept in context</p>
        <TypingHeadline />
        <span className="mt-6 block max-w-132.5 text-base leading-relaxed text-neutral-400">Each project isolates its sources, conversations, knowledge graph, and next actions.</span>
      </div>
      <small className="text-xs text-neutral-500">Grounded answers · attributed prompts · project-level access</small>
    </section>
    <section className="grid place-items-center bg-surface p-7.5 login-compact:min-h-screen">
      <form onSubmit={(event) => void submit(event)} className="[width:min(24.375rem,_100%)]">
        <div>
          <h2 className="m-0 text-3xl tracking-title text-neutral-50">Sign in</h2>
          <p className="mt-2.25 mb-7.5 text-sm text-neutral-500">Use one of the seeded team accounts.</p>
        </div>
        <LoginField label="Email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} />
        <LoginField
          label="Password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        {(error || externalError) && <p className="mt-3 mb-0 text-xs text-danger">
          {error || externalError}
        </p>}
        <button
          type="submit"
          disabled={loading}
          className="mt-5 h-11.25 w-full rounded-lg border-0 bg-neutral-100 font-bold text-neutral-900 disabled:opacity-50"
        >
          {loading ? 'Signing in…' : 'Sign in'}
        </button>
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
      if (currentLength >= LOGIN_HEADLINE.length)
        window.clearInterval(timer)
    }, 34)
    return () => window.clearInterval(timer)
  }, [])
  return <h1 aria-label={LOGIN_HEADLINE} className="relative m-0 max-w-160 text-hero leading-hero tracking-hero text-neutral-50">
    <span aria-hidden="true" className="invisible block">
      {LOGIN_HEADLINE}
    </span>
    <span aria-hidden="true" className="absolute inset-0">
      {LOGIN_HEADLINE.slice(0, length)}
      <i
        data-complete={length >= LOGIN_HEADLINE.length}
        className="[width:.055em] [height:.82em] [margin-left:.08em] [vertical-align:-.02em] inline-block animate-typing-cursor bg-neutral-50 data-[complete=true]:animate-typing-finish"
      />
    </span>
  </h1>
}
