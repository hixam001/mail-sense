// Executed inside Chromium: inspect computed text colors against opaque ancestors.
export function textContrast() {
  const rgb = value => value.match(/[\d.]+/g)?.map(Number)
  const luminance = color => color.slice(0, 3).map(value => {
    const channel = value / 255
    return channel <= .04045 ? channel / 12.92 : ((channel + .055) / 1.055) ** 2.4
  }).reduce((sum, value, index) => sum + value * [.2126, .7152, .0722][index], 0)
  const failures = []
  let samples = 0, minimum = Infinity
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT)
  while (walker.nextNode()) {
    const node = walker.currentNode, element = node.parentElement
    if (!node.textContent.trim() || !element?.getClientRects().length || element.closest(':disabled,script,style,option')) continue
    const style = getComputedStyle(element)
    if (style.visibility === 'hidden' || style.display === 'none') continue
    const foreground = rgb(element instanceof SVGElement ? style.fill : style.color)
    if (!foreground || foreground.length < 3 || foreground[3] === 0) continue
    let parent = element, background
    while (parent) {
      const candidate = rgb(getComputedStyle(parent).backgroundColor)
      if (candidate?.length === 3 || candidate?.[3] === 1) { background = candidate; break }
      parent = parent.parentElement
    }
    if (!background) continue
    const [high, low] = [luminance(foreground), luminance(background)].sort((a, b) => b - a)
    const ratio = (high + .05) / (low + .05)
    const size = parseFloat(style.fontSize)
    const large = size >= 24 || (size >= 18.66 && Number(style.fontWeight) >= 700)
    minimum = Math.min(minimum, ratio); samples++
    if (ratio + .01 < (large ? 3 : 4.5)) failures.push({ text: node.textContent.trim().slice(0, 40), ratio })
  }
  return { samples, minimum, failures }
}
