export function trimWhitespace(value) {
  const whitespace = character => /\p{White_Space}/u.test(character) ||
    (character.charCodeAt(0) >= 28 && character.charCodeAt(0) <= 31)
  let start = 0, end = value.length
  while (start < end && whitespace(value[start])) start++
  while (end > start && whitespace(value[end - 1])) end--
  return value.slice(start, end)
}

export function canonicalWord(value) {
  const normalized = trimWhitespace(value).normalize('NFC').toLowerCase()
  return Array.from(value).length <= 64 && /^[\p{L}\p{N}_]{2,}$/u.test(normalized) ? normalized : null
}

export function predictionInput(value) {
  const text = trimWhitespace(value)
  const length = Array.from(text).length
  const error = !length ? 'Add email subject or body text to classify.' : length > 50_000 ?
    'Text exceeds 50,000 trimmed characters. Shorten it before classifying; no text is truncated.' :
    !trimWhitespace(text.replace(/[\p{Cc}\p{Cs}]/gu, ' ')) ? 'Text must contain more than control characters.' : null
  return { text, length, error }
}

export function binomialInput(trials, successes) {
  const n = Number(trials), k = Number(successes)
  return trials !== '' && successes !== '' && Number.isInteger(n) && Number.isInteger(k) && n >= 1 && n <= 100 && k >= 0 && k <= n
}
