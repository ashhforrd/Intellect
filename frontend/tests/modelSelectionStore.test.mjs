import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import { runInNewContext } from 'node:vm'
import ts from 'typescript'

// Exercise browser preference behavior without a DOM or a live OpenAI request.
const source = readFileSync(new URL('../src/modelSelectionStore.ts', import.meta.url), 'utf8')
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText
const catalog = {
  default_model: 'gpt-6-luna', default_effort: 'medium',
  models: [
    { id: 'gpt-6-luna', default_effort: 'medium', reasoning_efforts: ['none', 'low', 'medium', 'high'] },
    { id: 'gpt-6-astra', default_effort: 'medium', reasoning_efforts: ['low', 'medium', 'high'] },
  ],
}

function setup({ models = async () => catalog, storage = new Map(), blocked = false } = {}) {
  const exports = {}
  runInNewContext(compiled, {
    exports,
    require(name) {
      if (name === 'react') return { useSyncExternalStore() {} }
      if (name === './api/client') return { api: { questions: { models } } }
      throw new Error(`Unexpected import: ${name}`)
    },
    window: {
      localStorage: {
        getItem(key) {
          if (blocked) throw new Error('Storage blocked')
          return storage.get(key) ?? null
        },
        setItem(key, value) {
          if (blocked) throw new Error('Storage blocked')
          storage.set(key, value)
        },
      },
    },
  })
  return { store: exports.modelSelectionStore, storage }
}

const signal = () => new AbortController().signal

test('preferences survive reload and remain scoped to account and project', async () => {
  const { store, storage } = setup()
  await store.load('alice', 'project-a', signal())
  store.select('alice', 'project-a', 'gpt-6-astra', 'high')
  await store.load('bob', 'project-a', signal())
  await store.load('alice', 'project-b', signal())
  assert.equal(store.getSnapshot('alice', 'project-a').selection.model, 'gpt-6-astra')
  assert.equal(store.getSnapshot('bob', 'project-a').selection.model, 'gpt-6-luna')
  assert.equal(store.getSnapshot('alice', 'project-b').selection.model, 'gpt-6-luna')
  const reloaded = setup({ storage }).store
  await reloaded.load('alice', 'project-a', signal())
  assert.equal(reloaded.getSnapshot('alice', 'project-a').selection.reasoning_effort, 'high')
})

test('switching models replaces unsupported effort and retains supported effort', async () => {
  const { store } = setup()
  await store.load('alice', 'project-a', signal())
  store.select('alice', 'project-a', 'gpt-6-luna', 'none')
  store.select('alice', 'project-a', 'gpt-6-astra')
  assert.equal(store.getSnapshot('alice', 'project-a').selection.reasoning_effort, 'medium')
  store.select('alice', 'project-a', 'gpt-6-astra', 'high')
  store.select('alice', 'project-a', 'gpt-6-luna')
  assert.equal(store.getSnapshot('alice', 'project-a').selection.reasoning_effort, 'high')
})

test('removed models, invalid efforts and malformed preferences fall back safely', async () => {
  for (const saved of [
    '{bad json',
    JSON.stringify({ model: 'removed', reasoning_effort: 'high' }),
    JSON.stringify({ model: 'gpt-6-astra', reasoning_effort: 'none' }),
  ]) {
    const { store } = setup({ storage: new Map([['intellect-answer-model:alice:project-a', saved]]) })
    await store.load('alice', 'project-a', signal())
    const state = store.getSnapshot('alice', 'project-a')
    assert.equal(state.selection.reasoning_effort, 'medium')
    assert.equal(state.error, null)
  }
})

test('blocked browser storage preserves the selection in memory', async () => {
  const { store } = setup({ blocked: true })
  await store.load('alice', 'project-a', signal())
  store.select('alice', 'project-a', 'gpt-6-astra', 'high')
  await store.load('alice', 'project-a', signal())
  assert.equal(store.getSnapshot('alice', 'project-a').selection.model, 'gpt-6-astra')
})

test('catalog failures visibly use server defaults and retry restores choices', async () => {
  let fail = true
  const { store } = setup({ models: async () => {
    if (fail) throw new Error('Offline')
    return catalog
  } })
  await store.load('alice', 'project-a', signal())
  assert.equal(store.getSnapshot('alice', 'project-a').selection, null)
  assert.match(store.getSnapshot('alice', 'project-a').error, /server default/)
  fail = false
  await store.load('alice', 'project-a', signal())
  assert.equal(store.getSnapshot('alice', 'project-a').error, null)
  assert.equal(store.getSnapshot('alice', 'project-a').selection.model, 'gpt-6-luna')
})

test('an aborted catalog load cannot overwrite a newer selection', async () => {
  let complete
  let calls = 0
  const { store } = setup({ models: () => ++calls === 1
    ? new Promise(resolve => { complete = resolve }) : Promise.resolve(catalog) })
  const controller = new AbortController()
  const firstLoad = store.load('alice', 'project-a', controller.signal)
  controller.abort()
  await store.load('alice', 'project-a', signal())
  store.select('alice', 'project-a', 'gpt-6-astra', 'high')
  complete(catalog)
  await firstLoad
  assert.equal(store.getSnapshot('alice', 'project-a').selection.model, 'gpt-6-astra')
})
