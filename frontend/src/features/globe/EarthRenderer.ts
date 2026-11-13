import {
  CustomBlending,
  OneFactor,
  BackSide,
  Group,
  LinearMipmapLinearFilter,
  Mesh,
  PerspectiveCamera,
  Raycaster,
  RepeatWrapping,
  Scene,
  ShaderMaterial,
  SphereGeometry,
  SRGBColorSpace,
  Texture,
  TextureLoader,
  Vector2,
  Vector3,
  WebGLRenderer,
} from 'three'
import {
  atmosphereFragment,
  atmosphereVertex,
  cloudFragment,
  cloudVertex,
  earthFragment,
  earthVertex,
} from './shaders'

export interface LatLng {
  lat: number
  lng: number
}

const FOV = 30
const TAU = Math.PI * 2
/** One full turn every 100 s — slow, calm, clearly alive. */
const SPIN_SPEED = TAU / 100
const TILT_MIN = -0.35
const TILT_MAX = 0.75

const easeInOut = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2)
const lerp = (a: number, b: number, t: number) => a + (b - a) * t

/** Unit-sphere point for lat/lng, matching three's SphereGeometry UV layout. */
export function latLngToVector(lat: number, lng: number, r = 1): Vector3 {
  const phi = ((lng + 180) * Math.PI) / 180
  const theta = ((90 - lat) * Math.PI) / 180
  return new Vector3(-Math.cos(phi) * Math.sin(theta), Math.cos(theta), Math.sin(phi) * Math.sin(theta)).multiplyScalar(r)
}

/** Spin angle that brings `lng` to face the camera. */
const spinFor = (lng: number) => Math.PI / 2 - ((lng + 180) * Math.PI) / 180

interface Layout {
  /** Globe centre as a fraction of the viewport. */
  cx: number
  cy: number
  /** Globe radius as a fraction of viewport height. */
  r: number
}

interface Tween {
  from: number
  to: number
  start: number
  dur: number
  ease: (t: number) => number
  set: (v: number) => void
  done?: () => void
}

export class EarthRenderer {
  readonly canvas: HTMLCanvasElement
  private renderer: WebGLRenderer
  private scene = new Scene()
  private camera = new PerspectiveCamera(FOV, 1, 0.01, 100)
  private earth = new Group()
  private cloudMat: ShaderMaterial
  private earthMat: ShaderMaterial
  private atmoMat: ShaderMaterial
  private earthMesh: Mesh
  private raf = 0
  private last = 0
  private tweens: Tween[] = []
  private reduceMotion: boolean

  // Orientation state: earth = Rx(tilt) · Ry(spin)
  private spin = spinFor(122)
  private tilt = 0.3
  private spinVel = 0
  private tiltVel = 0
  autoRotate = true
  private dragging = false

  private layout: Layout = { cx: 0.77, cy: 0.66, r: 0.6 }
  /**
   * Externally driven camera (during the globe ⇄ map transition):
   * `mapZoom` is a web-map zoom level matched at latitude `lat`; `fx, fy` is
   * where the point facing the viewer sits on screen. null = home framing.
   */
  private drive: { mapZoom: number; lat: number; fx: number; fy: number } | null = null
  private size = new Vector2(1, 1)

  onFrame?: () => void

  constructor(host: HTMLElement) {
    this.reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    this.renderer = new WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' })
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    this.renderer.outputColorSpace = SRGBColorSpace
    this.canvas = this.renderer.domElement
    host.appendChild(this.canvas)

    const sunDir = new Vector3(0.75, 0.42, 0.55).normalize()
    const blank = new Texture()
    const shared = { sunDir: { value: sunDir }, cloudOffset: { value: 0 } }

    this.earthMat = new ShaderMaterial({
      vertexShader: earthVertex,
      fragmentShader: earthFragment,
      uniforms: {
        ...shared,
        dayMap: { value: blank },
        maskMap: { value: blank },
        cloudMap: { value: blank },
        texel: { value: new Vector2(1 / 4096, 1 / 2048) },
      },
    })
    this.cloudMat = new ShaderMaterial({
      vertexShader: cloudVertex,
      fragmentShader: cloudFragment,
      uniforms: { ...shared, cloudMap: { value: blank } },
      transparent: true,
      depthWrite: false,
    })
    this.atmoMat = new ShaderMaterial({
      vertexShader: atmosphereVertex,
      fragmentShader: atmosphereFragment,
      uniforms: { sunDir: shared.sunDir },
      side: BackSide,
      blending: CustomBlending,
      blendSrc: OneFactor,
      blendDst: OneFactor,
      blendSrcAlpha: OneFactor,
      blendDstAlpha: OneFactor,
      transparent: true,
      depthWrite: false,
    })

    this.earthMesh = new Mesh(new SphereGeometry(1, 192, 128), this.earthMat)
    const clouds = new Mesh(new SphereGeometry(1.007, 160, 112), this.cloudMat)
    const atmosphere = new Mesh(new SphereGeometry(1.02, 160, 120), this.atmoMat)
    this.earth.add(this.earthMesh, clouds)
    this.scene.add(this.earth, atmosphere)

    this.loadTextures()
    this.bindPointer()
    this.loop = this.loop.bind(this)
    this.raf = requestAnimationFrame(this.loop)
  }

  // ---------- textures ----------
  private loadTextures() {
    const loader = new TextureLoader()
    const aniso = this.renderer.capabilities.getMaxAnisotropy()
    const prep = (t: Texture, srgb: boolean) => {
      t.anisotropy = aniso
      t.minFilter = LinearMipmapLinearFilter
      if (srgb) t.colorSpace = SRGBColorSpace
      t.needsUpdate = true
      return t
    }
    loader.load('/textures/earth-day-4k.jpg', (t) => {
      this.earthMat.uniforms.dayMap.value = prep(t, true)
      // Upgrade to 8K where the GPU allows it.
      if (this.renderer.capabilities.maxTextureSize >= 8192 && window.innerWidth >= 900) {
        loader.load('/textures/earth-day-8k.jpg', (hi) => {
          this.earthMat.uniforms.dayMap.value = prep(hi, true)
          t.dispose()
        })
      }
    })
    loader.load('/textures/earth-bump-mask-4k.jpg', (t) => {
      this.earthMat.uniforms.maskMap.value = prep(t, false)
    })
    loader.load('/textures/earth-clouds-4k.jpg', (t) => {
      // Clouds drift via a UV offset, so u runs past 1: wrap instead of clamping,
      // or the last texel column smears into latitude streaks.
      t.wrapS = RepeatWrapping
      prep(t, false)
      this.earthMat.uniforms.cloudMap.value = t
      this.cloudMat.uniforms.cloudMap.value = t
    })
  }

  // ---------- layout ----------
  setLayout(layout: Layout) {
    this.layout = layout
    this.applyCamera()
  }

  resize(w: number, h: number) {
    this.size.set(w, h)
    this.renderer.setSize(w, h, false)
    this.camera.aspect = w / h
    this.applyCamera()
  }

  private get tanHalf() {
    return Math.tan(((FOV / 2) * Math.PI) / 180)
  }
  /** Camera distance (earth radii from centre) for the home framing. */
  private get homeDistance() {
    return Math.sqrt(1 + (1 / (2 * this.layout.r * this.tanHalf)) ** 2)
  }
  /** Screen pixels per radian of ground at the point facing the camera. */
  private pxPerRadian(d: number) {
    return this.size.y / 2 / (this.tanHalf * (d - 1))
  }

  /** Web-map zoom equal in scale to the home framing, at latitude `lat`. */
  homeMapZoom(lat: number) {
    const p = this.pxPerRadian(this.homeDistance)
    return Math.log2((p * TAU * Math.cos((lat * Math.PI) / 180)) / 256)
  }

  /** Drive the camera from outside (null returns to the home framing). */
  setDrive(drive: { mapZoom: number; lat: number; fx: number; fy: number } | null) {
    this.drive = drive
  }

  get homeCentre() {
    return { fx: this.layout.cx, fy: this.layout.cy }
  }

  private applyCamera() {
    const { x: w, y: h } = this.size
    let d = this.homeDistance
    let fx = this.layout.cx
    let fy = this.layout.cy
    if (this.drive) {
      // Invert homeMapZoom: pixels per radian a web map shows at this zoom/latitude.
      const cosLat = Math.max(0.05, Math.cos((this.drive.lat * Math.PI) / 180))
      const p = (256 * 2 ** this.drive.mapZoom) / (TAU * cosLat)
      d = 1 + h / (2 * this.tanHalf * p)
      fx = this.drive.fx
      fy = this.drive.fy
    }
    this.camera.position.set(0, 0, d)
    this.camera.near = Math.max(0.0005, (d - 1) * 0.5)
    this.camera.lookAt(0, 0, 0)
    this.camera.setViewOffset(w, h, -(fx - 0.5) * w, -(fy - 0.5) * h, w, h)
    this.camera.updateProjectionMatrix()
  }

  // ---------- interaction: rotate only, never zoom ----------
  private bindPointer() {
    const el = this.canvas
    let lastX = 0
    let lastY = 0
    let lastT = 0
    el.addEventListener('pointerdown', (e) => {
      if (!this.hitsGlobe(e.clientX, e.clientY)) return
      this.dragging = true
      this.spinVel = this.tiltVel = 0
      lastX = e.clientX
      lastY = e.clientY
      lastT = performance.now()
      el.setPointerCapture(e.pointerId)
      el.classList.add('is-dragging')
    })
    el.addEventListener('pointermove', (e) => {
      el.classList.toggle('is-over', this.hitsGlobe(e.clientX, e.clientY))
      if (!this.dragging) return
      const k = 1 / (this.layout.r * this.size.y)
      const dx = (e.clientX - lastX) * k
      const dy = (e.clientY - lastY) * k
      const dt = Math.max(1, performance.now() - lastT) / 1000
      this.spin += dx
      this.tilt = Math.min(TILT_MAX, Math.max(TILT_MIN, this.tilt + dy))
      this.spinVel = dx / dt
      this.tiltVel = dy / dt
      lastX = e.clientX
      lastY = e.clientY
      lastT = performance.now()
    })
    const end = (e: PointerEvent) => {
      if (!this.dragging) return
      this.dragging = false
      el.releasePointerCapture(e.pointerId)
      el.classList.remove('is-dragging')
    }
    el.addEventListener('pointerup', end)
    el.addEventListener('pointercancel', end)
  }

  private raycaster = new Raycaster()
  private ndc(x: number, y: number) {
    const rect = this.canvas.getBoundingClientRect()
    return new Vector2(((x - rect.left) / rect.width) * 2 - 1, -((y - rect.top) / rect.height) * 2 + 1)
  }
  hitsGlobe(x: number, y: number) {
    this.raycaster.setFromCamera(this.ndc(x, y), this.camera)
    return this.raycaster.intersectObject(this.earthMesh, false).length > 0
  }
  /** Geographic point under the pointer, or null off the globe. */
  pick(x: number, y: number): LatLng | null {
    this.raycaster.setFromCamera(this.ndc(x, y), this.camera)
    const hit = this.raycaster.intersectObject(this.earthMesh, false)[0]
    if (!hit?.uv) return null
    return { lat: hit.uv.y * 180 - 90, lng: hit.uv.x * 360 - 180 }
  }

  /** Screen position of a lat/lng and whether it faces the viewer. */
  project(lat: number, lng: number): { x: number; y: number; visible: boolean } {
    const p = latLngToVector(lat, lng, 1.005).applyMatrix4(this.earth.matrixWorld)
    const toCam = this.camera.position.clone().sub(p).normalize()
    const facing = p.clone().normalize().dot(toCam)
    const s = p.project(this.camera)
    return { x: ((s.x + 1) / 2) * this.size.x, y: ((1 - s.y) / 2) * this.size.y, visible: facing > 0.18 }
  }

  // ---------- choreography ----------
  private tween(from: number, to: number, dur: number, ease: (t: number) => number, set: (v: number) => void, done?: () => void) {
    this.tweens.push({ from, to, start: performance.now(), dur: this.reduceMotion ? 1 : dur, ease, set, done })
  }

  /** Turn the planet so `target` faces the viewer. */
  orient(target: LatLng, dur: number, done?: () => void) {
    this.tweens = []
    this.autoRotate = false
    this.spinVel = this.tiltVel = 0
    let goal = spinFor(target.lng)
    goal += Math.round((this.spin - goal) / TAU) * TAU
    const tiltGoal = Math.min(1.35, Math.max(-1.35, (target.lat * Math.PI) / 180))
    this.tween(this.spin, goal, dur, easeInOut, (v) => (this.spin = v))
    this.tween(this.tilt, tiltGoal, dur, easeInOut, (v) => (this.tilt = v), done)
  }

  /** Suggested duration for turning toward `target` (longer for far turns). */
  turnDuration(target: LatLng) {
    let goal = spinFor(target.lng)
    goal += Math.round((this.spin - goal) / TAU) * TAU
    const ang = Math.hypot(goal - this.spin, (target.lat * Math.PI) / 180 - this.tilt)
    return Math.min(2200, 700 + ang * 600)
  }

  /** Snap so `target` faces the viewer (used before zooming back out of the map). */
  orientInstant(target: LatLng) {
    this.tweens = []
    this.spinVel = this.tiltVel = 0
    let goal = spinFor(target.lng)
    goal += Math.round((this.spin - goal) / TAU) * TAU
    this.spin = goal
    this.tilt = (target.lat * Math.PI) / 180
  }

  /** Ease the tilt back to the resting view and resume the slow spin. */
  settle(dur = 1200) {
    this.tween(this.tilt, 0.3, dur, easeInOut, (v) => (this.tilt = v), () => (this.autoRotate = true))
  }

  // ---------- frame loop ----------
  private loop(now: number) {
    const dt = Math.min(0.05, (now - (this.last || now)) / 1000)
    this.last = now

    // Run completion callbacks after filtering: they may queue follow-up tweens.
    const finished: Array<() => void> = []
    this.tweens = this.tweens.filter((tw) => {
      const p = Math.min(1, Math.max(0, (now - tw.start) / tw.dur))
      tw.set(lerp(tw.from, tw.to, tw.ease(p)))
      if (p >= 1 && tw.done) finished.push(tw.done)
      return p < 1
    })
    finished.forEach((fn) => fn())

    if (!this.dragging && this.tweens.length === 0) {
      // Inertia after a drag, blending back into the auto spin.
      this.spin += this.spinVel * dt
      this.tilt = Math.min(TILT_MAX, Math.max(TILT_MIN, this.tilt + this.tiltVel * dt))
      const decay = Math.exp(-dt * 3.2)
      this.spinVel *= decay
      this.tiltVel *= decay
      if (this.autoRotate && !this.reduceMotion) this.spin += SPIN_SPEED * dt
    }

    this.earth.rotation.set(this.tilt, this.spin, 0, 'XYZ')
    // Kept in [0, 1) so float precision never degrades on long-open tabs.
    this.earthMat.uniforms.cloudOffset.value = ((now / 1000) * 0.0004) % 1 // clouds drift slightly faster
    this.applyCamera()
    this.renderer.render(this.scene, this.camera)
    this.onFrame?.()
    this.raf = requestAnimationFrame(this.loop)
  }

  dispose() {
    cancelAnimationFrame(this.raf)
    this.renderer.dispose()
    this.canvas.remove()
  }
}
