// Render overlay.html frame by frame (30 fps, transparent PNG) from timeline.json.
// Usage: node render_overlay.mjs <overlayDir> <timeline.json> <outDir> [onlyFrame]
import { chromium } from 'playwright-core'
import { readFileSync, mkdirSync } from 'node:fs'

const [, , dir, tlPath, out, only] = process.argv
const tl = JSON.parse(readFileSync(tlPath, 'utf8'))
mkdirSync(out, { recursive: true })
const b = await chromium.launch({ channel: 'chrome', headless: true })
const p = await b.newPage({ viewport: { width: 1920, height: 1080 } })
await p.goto('file://' + dir + '/overlay.html')
await p.evaluate((t) => window.setTimeline(t), tl)
await p.evaluate(() => document.fonts.ready)
const n = Math.round(tl.duration * 30)
const frames = only ? only.split(',').map(Number) : [...Array(n).keys()]
for (const i of frames) {
  await p.evaluate((t) => window.render(t), i / 30)
  await p.screenshot({ path: `${out}/${String(i).padStart(4, '0')}.png`, omitBackground: true })
}
await b.close()
console.log('frames', frames.length)
