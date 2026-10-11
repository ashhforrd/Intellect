import { useEffect, useId, useLayoutEffect, useRef, useState, type CSSProperties, type KeyboardEvent } from 'react'
import { createPortal } from 'react-dom'
import { useAuiState } from '@assistant-ui/react'
import { Check, ChevronDown } from 'lucide-react'
import { useAuth } from '../authStore'
import { modelSelectionStore, useModelSelection } from '../modelSelectionStore'
import type { ReasoningEffort } from '../api/types'

const effortLabels: Record<ReasoningEffort, string> = {
  none: 'None', low: 'Low', medium: 'Medium', high: 'High', xhigh: 'Extra high', max: 'Maximum',
}

export function ModelPicker({ projectId }: { projectId: string }) {
  const { user } = useAuth()
  const accountId = user?.id ?? ''
  const { catalog, selection, loading, error } = useModelSelection(accountId, projectId)
  const running = useAuiState(state => state.thread.isRunning)
  const [retry, setRetry] = useState(0)
  const [open, setOpen] = useState(false)
  const [position, setPosition] = useState({ top: 0, left: 0 })
  const triggerRef = useRef<HTMLButtonElement>(null)
  const popupRef = useRef<HTMLDivElement>(null)
  const popupId = useId()
  const effortId = useId()
  const descriptionId = useId()
  useEffect(() => {
    if (!accountId) return
    const controller = new AbortController()
    void modelSelectionStore.load(accountId, projectId, controller.signal)
    return () => controller.abort()
  }, [accountId, projectId, retry])

  const model = catalog?.models.find(item => item.id === selection?.model)
  const efforts = model?.reasoning_efforts ?? []
  const effortIndex = Math.max(0, efforts.indexOf(selection?.reasoning_effort ?? 'medium'))
  const progress = efforts.length > 1 ? effortIndex / (efforts.length - 1) * 100 : 0
  const visible = open && !running

  if (running && open) setOpen(false)
  useLayoutEffect(() => {
    if (!visible) return
    function placePopup() {
      if (!triggerRef.current || !popupRef.current) return
      const trigger = triggerRef.current.getBoundingClientRect()
      const popup = popupRef.current.getBoundingClientRect()
      setPosition({
        top: Math.max(8, trigger.top - popup.height - 8),
        left: Math.max(8, Math.min(trigger.right - popup.width, window.innerWidth - popup.width - 8)),
      })
    }
    placePopup()
    window.addEventListener('resize', placePopup)
    window.addEventListener('scroll', placePopup, true)
    return () => {
      window.removeEventListener('resize', placePopup)
      window.removeEventListener('scroll', placePopup, true)
    }
  }, [visible, loading, error])

  useEffect(() => {
    if (!visible) return
    const focusTarget = popupRef.current?.querySelector<HTMLButtonElement>('button[data-selected="true"]')
      ?? popupRef.current?.querySelector<HTMLButtonElement>('button')
    const initialFocus = focusTarget ?? popupRef.current
    initialFocus?.focus({ preventScroll: true })
    function dismissOnOutside(event: PointerEvent) {
      if (!(event.target instanceof Node)) return
      if (!popupRef.current?.contains(event.target) && !triggerRef.current?.contains(event.target)) setOpen(false)
    }
    function dismissOnEscape(event: globalThis.KeyboardEvent) {
      if (event.key !== 'Escape') return
      event.preventDefault()
      setOpen(false)
      triggerRef.current?.focus()
    }
    document.addEventListener('pointerdown', dismissOnOutside)
    document.addEventListener('keydown', dismissOnEscape)
    return () => {
      document.removeEventListener('pointerdown', dismissOnOutside)
      document.removeEventListener('keydown', dismissOnEscape)
    }
  }, [visible])

  function navigateModels(event: KeyboardEvent<HTMLDivElement>) {
    const items = Array.from(event.currentTarget.querySelectorAll<HTMLButtonElement>('button'))
    const current = items.indexOf(document.activeElement as HTMLButtonElement)
    let next: number
    switch (event.key) {
      case 'ArrowDown': case 'ArrowRight': next = (current + 1) % items.length; break
      case 'ArrowUp': case 'ArrowLeft': next = (current - 1 + items.length) % items.length; break
      case 'Home': next = 0; break
      case 'End': next = items.length - 1; break
      default: return
    }
    event.preventDefault()
    const target = items[next]
    if (target?.dataset.model) modelSelectionStore.select(accountId, projectId, target.dataset.model)
    target?.focus()
  }

  return <>
    <button ref={triggerRef} type="button" disabled={running}
      aria-label={`Answer model: ${model?.label ?? 'Server default'}. Open model and effort settings`}
      aria-haspopup="dialog" aria-expanded={visible} aria-controls={visible ? popupId : undefined}
      onClick={() => setOpen(value => !value)}
      onKeyDown={event => {
        if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
          event.preventDefault()
          setOpen(true)
        }
      }}
      className="flex h-9 min-w-0 items-center gap-1.5 rounded-lg border-0 bg-transparent px-2 py-0 text-xs text-neutral-400 hover:bg-neutral-800 hover:text-neutral-100 focus-visible:ring-2 focus-visible:ring-neutral-400 disabled:cursor-default disabled:opacity-50">
      <span className="truncate">{loading ? 'Loading models…' : model?.label ?? 'Server default'}</span>
      <ChevronDown size={14} className={`shrink-0 transition-transform ${visible ? 'rotate-180' : ''}`} />
    </button>
    {visible && createPortal(
      <div ref={popupRef} id={popupId} role="dialog" aria-label="Model and reasoning effort" tabIndex={-1}
        style={position}
        onBlur={event => {
          const target = event.relatedTarget
          if (target instanceof Node && !event.currentTarget.contains(target) && !triggerRef.current?.contains(target)) setOpen(false)
        }}
        className="fixed z-50 max-h-[calc(100dvh-1rem)] w-68 max-w-[calc(100vw-1rem)] overflow-y-auto rounded-xl border border-neutral-700 bg-neutral-900 p-1.5 text-neutral-100 shadow-dialog">
        {error ? <div className="p-2.5 text-xs leading-body text-neutral-400" role="status">
          <p className="m-0">{error}</p>
          <button type="button" onClick={() => setRetry(value => value + 1)}
            className="mt-2 rounded-lg border border-neutral-700 bg-transparent px-2.5 py-1.5 text-xs text-neutral-200 hover:bg-neutral-800 focus-visible:ring-2 focus-visible:ring-neutral-400">Retry</button>
        </div> : <>
          <div className="px-2.5 pt-2 pb-1.5 text-2xs text-neutral-500">Answer model</div>
          {loading && !catalog && <p className="m-0 p-2.5 text-xs text-neutral-400" role="status">Loading models…</p>}
          <div role="radiogroup" aria-label="Answer model" onKeyDown={navigateModels}>
            {catalog?.models.map(item => <button key={item.id} type="button" role="radio"
              data-model={item.id} data-selected={item.id === model?.id} aria-checked={item.id === model?.id}
              tabIndex={item.id === model?.id ? 0 : -1} disabled={loading}
              onClick={() => modelSelectionStore.select(accountId, projectId, item.id)}
              className="flex w-full items-center justify-between gap-3 rounded-lg border-0 bg-transparent px-2.5 py-2.5 text-left text-xs text-neutral-300 hover:bg-neutral-800 hover:text-neutral-100 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-neutral-400 data-[selected=true]:bg-neutral-800 data-[selected=true]:text-neutral-50">
              {item.label}
              {item.id === model?.id && <Check size={14} aria-hidden="true" />}
            </button>)}
          </div>
          <div className="mt-1.5 border-t border-neutral-700 px-2.5 pt-3 pb-2.5">
            <div className="mb-3 flex items-center justify-between gap-3 text-xs">
              <label htmlFor={effortId} className="text-neutral-300">Reasoning effort</label>
              <span className="text-neutral-100">{selection ? effortLabels[selection.reasoning_effort] : '—'}</span>
            </div>
            <input id={effortId} type="range" min={0} max={Math.max(0, efforts.length - 1)} step={1}
              value={effortIndex} disabled={loading || efforts.length < 2}
              aria-valuetext={selection ? effortLabels[selection.reasoning_effort] : undefined}
              aria-describedby={descriptionId}
              style={{ '--effort-track': `linear-gradient(to right, var(--color-neutral-200) ${progress}%, var(--color-neutral-700) ${progress}%)` } as CSSProperties}
              onChange={event => {
                const effort = efforts[Number(event.target.value)]
                if (model && effort) modelSelectionStore.select(accountId, projectId, model.id, effort)
              }}
              className="model-effort-slider" />
            <div className="mt-2 flex justify-between text-2xs text-neutral-500" aria-hidden="true">
              <span>{efforts[0] ? effortLabels[efforts[0]] : '—'}</span>
              <span>{efforts.at(-1) ? effortLabels[efforts.at(-1)!] : '—'}</span>
            </div>
            <p id={descriptionId} className="mt-2.5 mb-0 text-2xs leading-copy text-neutral-500">Higher effort can take longer and use more tokens.</p>
          </div>
        </>}
      </div>, document.body,
    )}
  </>
}
