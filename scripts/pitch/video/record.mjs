// Drives the real FieldShift UI in a kiosk Chrome window and records each shot with x11grab.
// Usage: node record.mjs <outDir> [shotName...]
import { chromium } from 'playwright-core'
import { spawn } from 'node:child_process'

const OUT = process.argv[2]
const ONLY = new Set(process.argv.slice(3))
const BASE = 'http://localhost:5180/'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

function startRec(name) {
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'x11grab', '-draw_mouse', '0', '-framerate', '30',
    '-video_size', '1920x1080', '-i', `${process.env.DISPLAY || ':1'}.0+0,0`,
    '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '12', '-pix_fmt', 'yuv420p', `${OUT}/${name}.mkv`],
    { stdio: ['pipe', 'inherit', 'inherit'] })
  return async () => { ff.stdin.write('q'); await new Promise((r) => ff.on('close', r)) }
}

// Soft cursor with click ripple, drawn by the page so synthetic mouse events are visible.
const CURSOR = `
addEventListener('DOMContentLoaded', () => {
  const c = document.createElement('div')
  c.id = '__cur'
  c.style.cssText = 'position:fixed;left:0;top:0;width:22px;height:22px;margin:-11px 0 0 -11px;border-radius:50%;background:rgba(255,255,255,.92);box-shadow:0 0 0 2px rgba(0,0,0,.35),0 4px 14px rgba(0,0,0,.45);pointer-events:none;z-index:2147483647;transition:transform .12s;opacity:0'
  document.body.appendChild(c)
  addEventListener('mousemove', (e) => { c.style.opacity = 1; c.style.transform = 'translate(' + e.clientX + 'px,' + e.clientY + 'px)' }, true)
  addEventListener('mousedown', (e) => {
    const r = document.createElement('div')
    r.style.cssText = 'position:fixed;left:' + e.clientX + 'px;top:' + e.clientY + 'px;width:16px;height:16px;margin:-8px 0 0 -8px;border-radius:50%;border:2px solid #a6e07a;pointer-events:none;z-index:2147483646;transition:all .55s ease-out;opacity:1'
    document.body.appendChild(r)
    requestAnimationFrame(() => { r.style.transform = 'scale(4)'; r.style.opacity = 0 })
    setTimeout(() => r.remove(), 700)
  }, true)
})`

async function glide(page, x, y, ms = 700) {
  await page.mouse.move(x, y, { steps: Math.max(8, Math.round(ms / 16)) })
}
async function clickAt(page, x, y, ms = 700) {
  await glide(page, x, y, ms)
  await sleep(120)
  await page.mouse.down(); await sleep(60); await page.mouse.up()
}
async function center(loc) {
  const b = await loc.boundingBox()
  return [b.x + b.width / 2, b.y + b.height / 2]
}
// Eased scroll of the app's scroll container (or the document) to a target element/offset.
async function smoothScroll(page, target, ms) {
  await page.evaluate(async ({ target, ms }) => {
    const el = [...document.querySelectorAll('main, .shell__content')].find((e) => e.scrollHeight > e.clientHeight + 4) || document.scrollingElement
    const from = el.scrollTop
    let to = typeof target === 'number' ? target : 0
    if (typeof target === 'string') {
      const t = [...document.querySelectorAll('body *')].filter((n) => n.textContent.includes(target)).pop()
      if (t) to = from + t.getBoundingClientRect().top - 140
    }
    const t0 = performance.now()
    await new Promise((done) => {
      const step = (now) => {
        const k = Math.min(1, (now - t0) / ms)
        const e = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2
        el.scrollTop = from + (to - from) * e
        k < 1 ? requestAnimationFrame(step) : done()
      }
      requestAnimationFrame(step)
    })
  }, { target, ms })
}

const shots = {
  // Globe → Sóc Trăng → globe-to-map handover.
  async landing(page) {
    await page.goto(BASE, { waitUntil: 'networkidle' }); await sleep(5000)
    await glide(page, 1500, 600, 10)
    const stop = startRec('landing'); await sleep(1500)
    await clickAt(page, ...(await center(page.getByRole('button', { name: 'Sóc Trăng' }))), 900)
    await sleep(3200)
    await clickAt(page, ...(await center(page.getByRole('button', { name: 'Khoanh thửa ruộng' }))), 800)
    await sleep(5500)
    await stop()
  },
  // El Niño year-outlook banner on the recommendation screen.
  async outlook(page) {
    await page.goto(BASE + '#/de-xuat?thua=fld_soctrang', { waitUntil: 'networkidle' }); await sleep(4000)
    await glide(page, 1700, 300, 10)
    const stop = startRec('outlook'); await sleep(600)
    await smoothScroll(page, 'Mùa khô 2026', 1800)
    await sleep(500)
    await glide(page, 900, 470, 1200)
    await sleep(3500)
    await stop()
  },
  // Draw a parcel on satellite imagery in Sóc Trăng.
  async draw(page) {
    await page.goto(BASE + '#/ruong/moi?lat=9.5540&lng=106.0105&z=16.6&noi=S%C3%B3c%20Tr%C4%83ng', { waitUntil: 'networkidle' })
    await sleep(7000)
    await glide(page, 1500, 300, 10)
    const stop = startRec('draw'); await sleep(500)
    const pts = [[942, 252], [1224, 228], [1230, 352], [962, 414]]
    for (const [x, y] of pts) { await clickAt(page, x, y, 420); await sleep(140) }
    await page.keyboard.press('Enter')
    await sleep(1200)
    await clickAt(page, ...(await center(page.getByRole('button', { name: /Tiếp tục/ }))), 700)
    await sleep(2200)
    await stop()
  },
  // Digital twin: chart + 3D cut-away blocks play week by week, then rotate a block.
  async twin(page) {
    await page.goto(BASE + '#/mo-phong?thua=fld_soctrang', { waitUntil: 'networkidle' }); await sleep(4000)
    await page.getByRole('button', { name: 'Xem ruộng 3D' }).click(); await sleep(3500)
    await smoothScroll(page, 'Nước tưới đến tuần này', 10); await sleep(300)
    await page.evaluate(() => { const m = document.querySelector('main'); m.scrollTop -= 40 })
    await sleep(1500)
    await glide(page, 1700, 250, 10)
    const stop = startRec('twin'); await sleep(500)
    await clickAt(page, ...(await center(page.locator('.tw-play'))), 800)
    await sleep(15000)
    const b = await page.locator('.tw-3d canvas').last().boundingBox()
    await glide(page, b.x + b.width * 0.5, b.y + b.height * 0.55, 600)
    await page.mouse.down()
    await page.mouse.move(b.x + b.width * 0.75, b.y + b.height * 0.5, { steps: 60 })
    await page.mouse.up()
    await sleep(1200)
    await stop()
  },
  // The answer: 84 / 177 days and the crop timeline.
  async answer(page) {
    await page.goto(BASE + '#/de-xuat?thua=fld_soctrang', { waitUntil: 'networkidle' }); await sleep(5000)
    await smoothScroll(page, 'Engine đề xuất', 10); await sleep(1500)
    await glide(page, 1600, 250, 10)
    const stop = startRec('answer'); await sleep(800)
    await smoothScroll(page, 'Cây trùng mùa mặn', 2600)
    await glide(page, 470, 380, 1200)
    await sleep(3500)
    await stop()
  },
  // Evidence: every number has a source.
  async sources(page) {
    await page.goto(BASE + '#/nguon', { waitUntil: 'networkidle' }); await sleep(3500)
    await glide(page, 1700, 200, 10)
    const stop = startRec('sources'); await sleep(500)
    await smoothScroll(page, 'Quyết định', 2500)
    await sleep(500)
    await smoothScroll(page, 'Bằng chứng', 2000)
    await sleep(1500)
    await stop()
  },
}

const browser = await chromium.launch({
  channel: 'chrome', headless: false,
  args: ['--kiosk', '--window-position=0,0', '--window-size=1920,1080', '--ignore-gpu-blocklist',
    '--disable-backgrounding-occluded-windows', '--disable-renderer-backgrounding', '--hide-scrollbars',
    '--disable-infobars', '--force-device-scale-factor=1', '--disable-features=Translate,TranslateUI', '--lang=vi', '--accept-lang=vi'], env: { ...process.env, LANGUAGE: 'vi' },
  ignoreDefaultArgs: ['--enable-automation'],
})
const ctx = await browser.newContext({ viewport: null })
await ctx.addInitScript(CURSOR)
await ctx.addInitScript(() => { const s = document.createElement('style'); s.textContent = '::-webkit-scrollbar{display:none} *{scrollbar-width:none}'; document.documentElement.appendChild(s) })
const page = await ctx.newPage()
{
  const cdp = await ctx.newCDPSession(page)
  const { windowId } = await cdp.send('Browser.getWindowForTarget')
  await cdp.send('Browser.setWindowBounds', { windowId, bounds: { windowState: 'fullscreen' } })
  await sleep(1500)
}
if (process.env.PEEK) {
  await page.goto(BASE + process.env.PEEK, { waitUntil: 'networkidle' }); await sleep(7000)
  await page.screenshot({ path: OUT + '/peek.png' }); await browser.close(); process.exit(0)
}
for (const [name, fn] of Object.entries(shots)) {
  if (ONLY.size && !ONLY.has(name)) continue
  try { await fn(page); console.log('recorded', name) } catch (e) { console.log('FAILED', name, e.message) }
}
await browser.close()
