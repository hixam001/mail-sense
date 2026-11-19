export const API_ORIGIN = 'http://127.0.0.1:8000/api/v1'
const endpoints = new Set([
  '/health', '/dataset/summary', '/dataset/statistics', '/dataset/distributions',
  '/probability/word', '/probability/distributions', '/statistics/hypothesis-test',
  '/statistics/confidence-interval', '/predict', '/models/metrics',
  '/models/comparison', '/models/explanations',
])
export function query(path, parameters = {}) {
  return `${path}?${new URLSearchParams(parameters)}`
}
export async function apiFetch(path, { signal, body } = {}) {
  if (!endpoints.has(path.split('?')[0]) || path.includes('#') || path.includes('://')) {
    throw new Error('Unsupported local request.')
  }
  const response = await fetch(API_ORIGIN + path, {
    method: body === undefined ? 'GET' : 'POST',
    signal: AbortSignal.any([AbortSignal.timeout(15_000), ...(signal ? [signal] : [])]),
    credentials: 'omit', cache: 'no-store', redirect: 'error', referrerPolicy: 'no-referrer',
    ...(body === undefined ? {} : {
      headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
    }),
  })
  const result = await response.json()
  if (!response.ok) throw new Error(result.error?.message || 'The local request failed.')
  return result
}
