import { createHighlighter, type Highlighter } from 'shiki'

let _promise: Promise<Highlighter> | null = null

export function getHighlighter(): Promise<Highlighter> {
  return (_promise ??= createHighlighter({
    themes: ['github-dark'],
    langs: ['python', 'typescript', 'javascript', 'bash', 'json', 'text'],
  }))
}
