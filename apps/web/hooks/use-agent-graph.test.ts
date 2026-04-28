import { describe, it, expect } from 'vitest'
import { buildGraphState } from './use-agent-graph'
import type { RunEvent } from './use-run-stream'

function ev(type: RunEvent['type'], payload: Record<string, unknown> = {}): RunEvent {
  return { run_id: 'r1', type, payload }
}

describe('buildGraphState', () => {
  it('estado inicial: supervisor idle, sem workers, finalize idle', () => {
    const state = buildGraphState([])
    expect(state.supervisorStatus).toBe('idle')
    expect(state.tasks).toHaveLength(0)
    expect(state.finalizeStatus).toBe('idle')
  })

  it('agent_started → supervisor thinking', () => {
    const state = buildGraphState([ev('agent_started')])
    expect(state.supervisorStatus).toBe('thinking')
  })

  it('task_started → supervisor done, worker thinking', () => {
    const state = buildGraphState([
      ev('agent_started'),
      ev('task_started', { task: 'Tarefa 1', index: 0 }),
    ])
    expect(state.supervisorStatus).toBe('done')
    expect(state.tasks[0].status).toBe('thinking')
  })

  it('skill_called → label da skill no worker ativo', () => {
    const state = buildGraphState([
      ev('agent_started'),
      ev('task_started', { task: 'Tarefa 1', index: 0 }),
      ev('skill_called', { skill: 'web_search' }),
    ])
    expect(state.tasks[0].skill).toBe('web_search')
  })

  it('hitl_required → worker hitl_pending', () => {
    const state = buildGraphState([
      ev('agent_started'),
      ev('task_started', { task: 'Tarefa 1', index: 0 }),
      ev('hitl_required', { skill: 'code_interpreter', params: {} }),
    ])
    expect(state.tasks[0].status).toBe('hitl_pending')
  })

  it('hitl_resolved após hitl_required → worker volta a thinking', () => {
    const state = buildGraphState([
      ev('agent_started'),
      ev('task_started', { task: 'Tarefa 1', index: 0 }),
      ev('hitl_required', { skill: 'code_interpreter', params: {} }),
      ev('hitl_resolved', { decision: 'approve' }),
    ])
    expect(state.tasks[0].status).toBe('thinking')
  })

  it('task_completed done → worker done', () => {
    const state = buildGraphState([
      ev('agent_started'),
      ev('task_started', { task: 'Tarefa 1', index: 0 }),
      ev('task_completed', { task: 'Tarefa 1', status: 'done', index: 0 }),
    ])
    expect(state.tasks[0].status).toBe('done')
  })

  it('task_completed failed → worker failed', () => {
    const state = buildGraphState([
      ev('agent_started'),
      ev('task_started', { task: 'Tarefa 1', index: 0 }),
      ev('task_completed', { task: 'Tarefa 1', status: 'failed', index: 0 }),
    ])
    expect(state.tasks[0].status).toBe('failed')
  })

  it('dois workers criados quando dois task_started', () => {
    const state = buildGraphState([
      ev('agent_started'),
      ev('task_started', { task: 'T1', index: 0 }),
      ev('task_completed', { task: 'T1', status: 'done', index: 0 }),
      ev('task_started', { task: 'T2', index: 1 }),
    ])
    expect(state.tasks).toHaveLength(2)
    expect(state.tasks[0].status).toBe('done')
    expect(state.tasks[1].status).toBe('thinking')
  })

  it('run_completed → finalize done', () => {
    const state = buildGraphState([
      ev('run_completed', { tasks_count: 1 }),
    ])
    expect(state.finalizeStatus).toBe('done')
  })

  it('run_failed → finalize failed', () => {
    const state = buildGraphState([
      ev('run_failed', { error: 'Erro' }),
    ])
    expect(state.finalizeStatus).toBe('failed')
  })
})
