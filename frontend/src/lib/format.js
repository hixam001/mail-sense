export function formatNumber(value, percent = false) {
  if (value == null) return 'Undefined'
  if (percent) {
    if (value > 0 && value < .0001) return `${(value * 100).toExponential(2)}%`
    if (value < 1 && value >= .99995) return '>99.99%'
    return `${(value * 100).toFixed(2)}%`
  }
  return new Intl.NumberFormat('en', {
    maximumSignificantDigits: 6,
    notation: value !== 0 && (Math.abs(value) < .0001 || Math.abs(value) >= 1e9) ? 'scientific' : 'standard',
  }).format(value)
}
