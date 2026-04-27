import { createHighlighter, type Highlighter } from 'shiki'

let _highlighter: Highlighter | null = null

export async function getHighlighter(): Promise<Highlighter> {
  if (!_highlighter) {
    _highlighter = await createHighlighter({
      themes: ['github-dark'],
      langs: ['python', 'typescript', 'javascript', 'bash', 'json', 'text'],
    })
  }
  return _highlighter
}
