import { useSyncExternalStore } from 'react'
import { api, ApiError } from './api/client'
import type { Project } from './api/types'

type ProjectState = {
  projects: Project[]
  activeProjectId: string | null
  loading: boolean
  error: string | null
}

let state: ProjectState = {
  projects: [],
  activeProjectId: window.localStorage.getItem('intellect-active-project'),
  loading: false,
  error: null,
}
const listeners = new Set<() => void>()

function update(patch: Partial<ProjectState>) {
  state = { ...state, ...patch }
  listeners.forEach((listener) => listener())
}

function errorMessage(error: unknown) {
  return error instanceof ApiError ? error.message : 'Unable to load projects.'
}

export const projectStore = {
  getSnapshot: () => state,
  subscribe(listener: () => void) {
    listeners.add(listener)
    return () => listeners.delete(listener)
  },
  async load() {
    update({ loading: true, error: null })
    try {
      const projects = await api.projects.list()
      const activeProjectId = projects.some((item) => item.id === state.activeProjectId)
        ? state.activeProjectId
        : projects[0]?.id || null
      if (activeProjectId) window.localStorage.setItem('intellect-active-project', activeProjectId)
      update({ projects, activeProjectId, loading: false })
    } catch (error) {
      update({ loading: false, error: errorMessage(error) })
    }
  },
  select(projectId: string) {
    window.localStorage.setItem('intellect-active-project', projectId)
    update({ activeProjectId: projectId })
  },
  async create(name: string) {
    const project = await api.projects.create(name)
    update({ projects: [project, ...state.projects], activeProjectId: project.id })
    window.localStorage.setItem('intellect-active-project', project.id)
    return project
  },
}

export function useProjects() {
  return useSyncExternalStore(projectStore.subscribe, projectStore.getSnapshot)
}
