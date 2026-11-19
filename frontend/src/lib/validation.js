export function canonicalWord(value) {
  const normalized = value.trim().normalize('NFC').toLowerCase()
  return Array.from(value).length <= 64 && /^[\p{L}\p{N}_]{2,}$/u.test(normalized) ? normalized : null
}

export function binomialInput(trials, successes) {
  const n = Number(trials), k = Number(successes)
  return trials !== '' && successes !== '' && Number.isInteger(n) && Number.isInteger(k) && n >= 1 && n <= 100 && k >= 0 && k <= n
}
