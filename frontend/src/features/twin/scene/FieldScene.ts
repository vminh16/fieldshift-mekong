import {
  BoxGeometry,
  BufferGeometry,
  CanvasTexture,
  Color,
  DirectionalLight,
  DoubleSide,
  HemisphereLight,
  IcosahedronGeometry,
  InstancedMesh,
  Mesh,
  MeshBasicMaterial,
  MeshStandardMaterial,
  Object3D,
  PCFSoftShadowMap,
  PerspectiveCamera,
  PlaneGeometry,
  CylinderGeometry,
  Scene,
  SRGBColorSpace,
  Vector3,
  WebGLRenderer,
} from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js'

/** What the scene shows for one moment. Numbers come from the engine's twin week (interpolated). */
export interface FieldState {
  crop: 'rice' | 'legume' | 'cover' | 'other' | null
  /** 0..1 canopy development (drawing only, from the FAO stage). */
  growth: number
  /** 0..1 how ripe (late stage) — rice turns golden. */
  ripe: number
  pondMm: number
  rootM: number
  wet: number
  saltSeason: boolean
}

export interface Anchors {
  pond: { x: number; y: number; visible: boolean }
  root: { x: number; y: number; visible: boolean }
  canal: { x: number; y: number; visible: boolean }
  depth: { x: number; y: number }[]
}

// Scene units: plot 8 × 5, soil block 3 deep = 1.2 m.
const W = 8
const D = 5
const SOIL = 3
const PX_M = SOIL / 1.2
const DEPTH_MARKS = [0, 0.4, 0.8, 1.2]
const ROWS = 14
const COLS = 24
const PLANT_H = { rice: 1.0, legume: 0.55, cover: 0.2, other: 1.45 } as const

const COL = {
  soilTop: new Color('#4a3d2f'),
  soil: new Color('#2f2720'),
  bund: new Color('#5d6b3b'),
  water: new Color('#3b7cc4'),
  saltWater: new Color('#b08a3e'),
  riceYoung: new Color('#7fb35a'),
  riceMid: new Color('#4f8f3a'),
  riceRipe: new Color('#c9a648'),
  legume: new Color('#3f7d3a'),
  cover: new Color('#5c8a3e'),
  other: new Color('#6a9a3a'),
}

const ease = (cur: number, target: number, k: number) => cur + (target - cur) * k

// ---------- plant geometries (built once, shared) ----------
function blade(h: number, w: number, bend: number): BufferGeometry {
  const g = new PlaneGeometry(w, h, 1, 5)
  g.translate(0, h / 2, 0)
  const p = g.attributes.position
  for (let i = 0; i < p.count; i++) {
    const y = p.getY(i)
    const t = y / h
    p.setX(i, p.getX(i) * (1 - t * 0.85))
    p.setZ(i, bend * t * t)
  }
  g.computeVertexNormals()
  return g
}

function riceTuft(): BufferGeometry {
  const parts: BufferGeometry[] = []
  for (let k = 0; k < 9; k++) {
    const g = blade(0.75 + (k % 3) * 0.12, 0.05, 0.14 + (k % 2) * 0.1)
    g.rotateY((k / 9) * Math.PI * 2 + (k % 2) * 0.3)
    parts.push(g)
  }
  return mergeGeometries(parts)!
}

function legumeBush(): BufferGeometry {
  const parts: BufferGeometry[] = []
  const stem = new CylinderGeometry(0.012, 0.018, 0.6, 5)
  stem.translate(0, 0.3, 0)
  parts.push(stem)
  const leaves: [number, number, number, number][] = [
    [0, 0.6, 0, 0.17],
    [0.14, 0.48, 0.05, 0.14],
    [-0.13, 0.46, -0.04, 0.14],
    [0.03, 0.38, 0.14, 0.13],
    [-0.04, 0.36, -0.14, 0.12],
  ]
  for (const [x, y, z, r] of leaves) {
    const l = new IcosahedronGeometry(r, 1)
    l.scale(1, 0.55, 1)
    l.translate(x, y, z)
    parts.push(l)
  }
  return mergeGeometries(parts.map((p) => p.toNonIndexed()))!
}

function coverMat(): BufferGeometry {
  const parts: BufferGeometry[] = []
  for (let k = 0; k < 5; k++) {
    const l = new IcosahedronGeometry(0.11, 1)
    l.scale(1, 0.45, 1)
    const a = (k / 5) * Math.PI * 2
    l.translate(Math.cos(a) * 0.1, 0.06 + (k % 2) * 0.03, Math.sin(a) * 0.1)
    parts.push(l)
  }
  return mergeGeometries(parts)!
}

function tallStalk(): BufferGeometry {
  const parts: BufferGeometry[] = [new CylinderGeometry(0.02, 0.03, 1, 6).translate(0, 0.5, 0).toNonIndexed()]
  for (let k = 0; k < 5; k++) {
    const g = blade(0.55, 0.07, 0.25)
    g.rotateZ(0.9)
    g.rotateY(k * 2.4)
    g.translate(0, 0.25 + k * 0.13, 0)
    parts.push(g.toNonIndexed())
  }
  return mergeGeometries(parts)!
}

/** Soft vertical gradient + faint horizon lines for the cut faces of the soil block. */
function soilTexture(): CanvasTexture {
  const c = document.createElement('canvas')
  c.width = 64
  c.height = 256
  const x = c.getContext('2d')!
  const g = x.createLinearGradient(0, 0, 0, 256)
  g.addColorStop(0, '#4a3b2c')
  g.addColorStop(0.35, '#3a2f25')
  g.addColorStop(1, '#241e19')
  x.fillStyle = g
  x.fillRect(0, 0, 64, 256)
  x.globalAlpha = 0.18
  for (let i = 0; i < 700; i++) {
    x.fillStyle = Math.random() > 0.5 ? '#6b5a46' : '#151210'
    x.fillRect(Math.random() * 64, Math.random() * 256, 1, 1)
  }
  const t = new CanvasTexture(c)
  t.colorSpace = SRGBColorSpace
  return t
}

/** Fine root strokes drawn once, stretched over the root zone. */
function rootTexture(): CanvasTexture {
  const c = document.createElement('canvas')
  c.width = 512
  c.height = 128
  const x = c.getContext('2d')!
  x.strokeStyle = 'rgba(214, 226, 190, 0.5)'
  x.lineCap = 'round'
  for (let i = 0; i < 70; i++) {
    let px = Math.random() * 512
    let py = 0
    x.lineWidth = 1.2
    x.beginPath()
    x.moveTo(px, py)
    while (py < 128) {
      px += (Math.random() - 0.5) * 8
      py += 6 + Math.random() * 8
      x.lineTo(px, py)
      x.lineWidth = Math.max(0.3, x.lineWidth * 0.9)
    }
    x.stroke()
  }
  const t = new CanvasTexture(c)
  t.colorSpace = SRGBColorSpace
  return t
}

interface FaceOverlay {
  root: Mesh
  wet: Mesh
  line: Mesh
}

/**
 * A cut-away block of the parcel: bunded surface with instanced crops, standing water,
 * soil faces showing the root zone and root-zone wetness, and the canal behind.
 * Imperative like EarthRenderer; `setTarget` sets where the scene is heading and every frame eases
 * towards it, so scrubbing and playback stay smooth.
 */
export class FieldScene {
  readonly canvas: HTMLCanvasElement
  onFrame?: (a: Anchors) => void

  private renderer: WebGLRenderer
  private scene = new Scene()
  private camera = new PerspectiveCamera(30, 1, 0.1, 100)
  private controls: OrbitControls
  private raf = 0
  private last = 0
  private time = 0
  private visible = true
  private observer: IntersectionObserver

  private plants: Record<NonNullable<FieldState['crop']>, InstancedMesh> = {} as never
  private jitter: { x: number; z: number; rot: number; s: number; phase: number; l: number }[] = []
  private water: Mesh
  private canalMat: MeshStandardMaterial
  private faces: FaceOverlay[] = []
  private dummy = new Object3D()
  private tmpColor = new Color()
  private plantColor = new Color()

  private cur: FieldState = { crop: null, growth: 0, ripe: 0, pondMm: 0, rootM: 0, wet: 0, saltSeason: false }
  private target: FieldState = { ...this.cur }
  private saltMix = 0
  private reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

  constructor(host: HTMLElement) {
    this.renderer = new WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' })
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75))
    this.renderer.outputColorSpace = SRGBColorSpace
    this.renderer.shadowMap.enabled = true
    this.renderer.shadowMap.type = PCFSoftShadowMap
    this.canvas = this.renderer.domElement
    host.appendChild(this.canvas)

    this.camera.position.set(8.4, 5.7, 9.8)
    this.controls = new OrbitControls(this.camera, this.canvas)
    this.controls.target.set(-0.1, -0.85, -0.5)
    this.controls.enableDamping = true
    this.controls.enableZoom = false
    this.controls.enablePan = false
    this.controls.minAzimuthAngle = -0.15
    this.controls.maxAzimuthAngle = 1.25
    this.controls.minPolarAngle = 0.75
    this.controls.maxPolarAngle = 1.25
    this.controls.rotateSpeed = 0.5
    this.controls.update()

    // light: soft sky + warm low sun from the right, like the rest of the app
    this.scene.add(new HemisphereLight('#d8e6f2', '#3a2f26', 1.15))
    const sun = new DirectionalLight('#fff1d6', 2.1)
    sun.position.set(6, 10, 5)
    sun.castShadow = true
    sun.shadow.mapSize.set(1024, 1024)
    Object.assign(sun.shadow.camera, { left: -6, right: 6, top: 5, bottom: -5, near: 1, far: 30 })
    sun.shadow.bias = -0.0005
    this.scene.add(sun)

    this.buildGround()
    this.water = this.buildWater()
    this.canalMat = this.buildCanal()
    this.buildPlants()

    const ro = new ResizeObserver(() => this.resize())
    ro.observe(host)
    this.resize()
    // Pause when scrolled out of view: two WebGL scenes should not burn a laptop battery.
    this.observer = new IntersectionObserver(([e]) => (this.visible = e.isIntersecting))
    this.observer.observe(host)
    this.loop = this.loop.bind(this)
    this.raf = requestAnimationFrame(this.loop)
    ;(this as unknown as { ro: ResizeObserver }).ro = ro
  }

  setTarget(s: FieldState) {
    this.target = s
    if (this.cur.crop !== s.crop) {
      // New season: plants start from the ground instead of morphing between species.
      this.cur = { ...this.cur, crop: s.crop, growth: 0, ripe: 0 }
    }
  }

  dispose() {
    cancelAnimationFrame(this.raf)
    this.observer.disconnect()
    ;(this as unknown as { ro: ResizeObserver }).ro.disconnect()
    this.controls.dispose()
    this.scene.traverse((o) => {
      const m = o as Mesh
      m.geometry?.dispose()
      const mat = m.material as MeshStandardMaterial | MeshStandardMaterial[] | undefined
      ;(Array.isArray(mat) ? mat : mat ? [mat] : []).forEach((x) => {
        x.map?.dispose()
        x.dispose()
      })
    })
    this.renderer.dispose()
    this.canvas.remove()
  }

  // ---------- building ----------
  private buildGround() {
    const soilMat = new MeshStandardMaterial({ map: soilTexture(), roughness: 1 })
    const topMat = new MeshStandardMaterial({ color: COL.soilTop, roughness: 0.95 })
    // faces: +x, -x, +y, -y, +z, -z
    const block = new Mesh(new BoxGeometry(W, SOIL, D), [soilMat, soilMat, topMat, soilMat, soilMat, soilMat])
    block.position.y = -SOIL / 2
    block.receiveShadow = true
    this.scene.add(block)

    const bundMat = new MeshStandardMaterial({ color: COL.bund, roughness: 1 })
    const bund = (w: number, d: number, x: number, z: number) => {
      const b = new Mesh(new BoxGeometry(w, 0.16, d), bundMat)
      b.position.set(x, 0.08, z)
      b.castShadow = true
      b.receiveShadow = true
      this.scene.add(b)
    }
    bund(W, 0.18, 0, D / 2 - 0.09)
    bund(W, 0.18, 0, -D / 2 + 0.09)
    bund(0.18, D, W / 2 - 0.09, 0)
    bund(0.18, D, -W / 2 + 0.09, 0)

    // root zone + wetness overlays on the two faces the camera sees (front +z, right +x)
    const roots = rootTexture()
    const mk = (width: number, place: (m: Mesh) => void): FaceOverlay => {
      const root = new Mesh(new PlaneGeometry(width, 1), new MeshBasicMaterial({ map: roots, transparent: true, opacity: 0.9, depthWrite: false }))
      const wet = new Mesh(new PlaneGeometry(width, 1), new MeshBasicMaterial({ color: '#3f86d8', transparent: true, opacity: 0.33, depthWrite: false }))
      const line = new Mesh(new PlaneGeometry(width, 0.025), new MeshBasicMaterial({ color: '#c2e3a8', transparent: true, opacity: 0.85, depthWrite: false }))
      ;[root, wet, line].forEach((m) => {
        place(m)
        this.scene.add(m)
      })
      return { root, wet, line }
    }
    this.faces.push(mk(W, (m) => m.position.set(0, 0, D / 2 + 0.004)))
    this.faces.push(
      mk(D, (m) => {
        m.rotation.y = Math.PI / 2
        m.position.set(W / 2 + 0.004, 0, 0)
      }),
    )
    // depth ticks on the front-left edge
    const tickMat = new MeshBasicMaterial({ color: '#8b9388' })
    for (const d of DEPTH_MARKS) {
      const t = new Mesh(new PlaneGeometry(0.22, 0.02), tickMat)
      t.position.set(-W / 2 - 0.11, -d * PX_M, D / 2 + 0.004)
      this.scene.add(t)
    }
  }

  private buildWater(): Mesh {
    const mat = new MeshStandardMaterial({ color: COL.water, transparent: true, opacity: 0.62, roughness: 0.08, metalness: 0.15, depthWrite: false })
    const w = new Mesh(new BoxGeometry(W - 0.36, 1, D - 0.36), mat)
    w.visible = false
    this.scene.add(w)
    return w
  }

  private buildCanal(): MeshStandardMaterial {
    const bankMat = new MeshStandardMaterial({ color: '#3b3226', roughness: 1 })
    const bank = new Mesh(new BoxGeometry(W + 1.4, 0.7, 0.5), bankMat)
    bank.position.set(0.2, -0.35, -D / 2 - 1.55)
    bank.receiveShadow = true
    this.scene.add(bank)
    const bed = new Mesh(new BoxGeometry(W + 1.4, 0.2, 1.3), bankMat)
    bed.position.set(0.2, -0.9, -D / 2 - 0.65)
    this.scene.add(bed)
    const mat = new MeshStandardMaterial({ color: COL.water, transparent: true, opacity: 0.8, roughness: 0.1, metalness: 0.2 })
    const water = new Mesh(new BoxGeometry(W + 1.4, 0.5, 1.3), mat)
    water.position.set(0.2, -0.55, -D / 2 - 0.65)
    this.scene.add(water)
    return mat
  }

  private buildPlants() {
    const geos = { rice: riceTuft(), legume: legumeBush(), cover: coverMat(), other: tallStalk() }
    const n = ROWS * COLS
    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        this.jitter.push({
          x: -W / 2 + 0.45 + (c + 0.5) * ((W - 0.9) / COLS) + (Math.random() - 0.5) * 0.08,
          z: -D / 2 + 0.45 + (r + 0.5) * ((D - 0.9) / ROWS) + (Math.random() - 0.5) * 0.08,
          rot: Math.random() * Math.PI * 2,
          s: 0.85 + Math.random() * 0.3,
          phase: Math.random() * Math.PI * 2,
          // per-plant shade variation so a field never reads as one flat colour
          l: (Math.random() - 0.5) * 0.12,
        })
      }
    }
    for (const key of Object.keys(geos) as (keyof typeof geos)[]) {
      const mat = new MeshStandardMaterial({ color: '#ffffff', roughness: 0.75, side: DoubleSide })
      const mesh = new InstancedMesh(geos[key], mat, n)
      mesh.castShadow = true
      mesh.receiveShadow = true
      mesh.visible = false
      mesh.frustumCulled = false
      for (let i = 0; i < n; i++) mesh.setColorAt(i, COL[key === 'rice' ? 'riceMid' : key])
      this.scene.add(mesh)
      this.plants[key] = mesh
    }
  }

  // ---------- frame ----------
  private resize() {
    const host = this.canvas.parentElement!
    const w = host.clientWidth
    const h = host.clientHeight
    if (!w || !h) return
    this.renderer.setSize(w, h, false)
    this.camera.aspect = w / h
    // Keep the whole block in frame on narrow cards.
    this.camera.fov = w / h < 1.2 ? 38 : 30
    this.camera.updateProjectionMatrix()
  }

  private loop(now: number) {
    this.raf = requestAnimationFrame(this.loop)
    const dt = Math.min(0.05, (now - (this.last || now)) / 1000)
    this.last = now
    if (!this.visible) return
    this.time += dt
    const k = this.reduceMotion ? 1 : 1 - Math.exp(-dt * 7)
    const t = this.target
    const c = this.cur
    c.growth = ease(c.growth, t.growth, k)
    c.ripe = ease(c.ripe, t.ripe, k)
    c.pondMm = ease(c.pondMm, t.pondMm, k)
    c.rootM = ease(c.rootM, t.rootM, k)
    c.wet = ease(c.wet, t.wet, k)
    this.saltMix = ease(this.saltMix, t.saltSeason ? 1 : 0, k)

    this.updatePlants()
    this.updateSoil()
    this.controls.update()
    this.renderer.render(this.scene, this.camera)
    this.onFrame?.(this.anchors())
  }

  private updatePlants() {
    const c = this.cur
    for (const [key, mesh] of Object.entries(this.plants) as [NonNullable<FieldState['crop']>, InstancedMesh][]) {
      const on = key === c.crop && c.growth > 0.01
      mesh.visible = on
      if (!on) continue
      const h = PLANT_H[key] * Math.max(0.04, c.growth)
      // Legumes/cover stay compact so rows and soil between them remain visible.
      const spread = key === 'legume' ? 0.72 : key === 'cover' ? 0.9 : 1
      const wGrow = (0.45 + 0.55 * Math.min(1, c.growth * 1.4)) * spread
      const sway = this.reduceMotion ? 0 : 0.06 * c.growth
      if (key === 'rice') this.tmpColor.copy(COL.riceYoung).lerp(COL.riceMid, Math.min(1, c.growth * 1.5)).lerp(COL.riceRipe, c.ripe)
      else this.tmpColor.copy(COL[key])
      this.jitter.forEach((j, i) => {
        this.dummy.position.set(j.x, 0.02, j.z)
        this.dummy.rotation.set(Math.sin(this.time * 1.4 + j.phase) * sway, j.rot, Math.cos(this.time * 1.1 + j.phase) * sway * 0.6)
        this.dummy.scale.set(j.s * wGrow, (h / PLANT_H[key]) * j.s * PLANT_H[key], j.s * wGrow)
        this.dummy.updateMatrix()
        mesh.setMatrixAt(i, this.dummy.matrix)
        mesh.setColorAt(i, this.plantColor.copy(this.tmpColor).offsetHSL(j.l * 0.15, 0, j.l))
      })
      mesh.instanceMatrix.needsUpdate = true
      if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true
    }
  }

  private updateSoil() {
    const c = this.cur
    // standing water, exaggerated so 40 mm is visible on a 2 m block
    const pondH = Math.min(c.pondMm, 150) / 150 * 0.32
    this.water.visible = pondH > 0.01
    if (this.water.visible) {
      this.water.scale.y = pondH
      this.water.position.y = pondH / 2 + 0.005
    }
    const rootH = Math.min(c.rootM, 1.2) * PX_M
    for (const f of this.faces) {
      f.root.visible = rootH > 0.02
      f.root.scale.y = Math.max(0.001, rootH)
      f.root.position.y = -rootH / 2
      const wetH = rootH * Math.max(0, Math.min(1, c.wet))
      f.wet.visible = wetH > 0.02
      f.wet.scale.y = Math.max(0.001, wetH)
      f.wet.position.y = -rootH + wetH / 2
      f.line.visible = rootH > 0.02
      f.line.position.y = -rootH
    }
    this.canalMat.color.copy(COL.water).lerp(COL.saltWater, this.saltMix * 0.75)
  }

  private project(v: Vector3) {
    const p = v.clone().project(this.camera)
    const w = this.canvas.clientWidth
    const h = this.canvas.clientHeight
    return { x: (p.x * 0.5 + 0.5) * w, y: (-p.y * 0.5 + 0.5) * h, visible: p.z < 1 }
  }

  private anchors(): Anchors {
    const c = this.cur
    const rootY = -Math.min(c.rootM, 1.2) * PX_M
    const pond = this.project(new Vector3(-W / 2 + 0.6, 0.4, D / 2))
    const root = this.project(new Vector3(-W / 2 + 0.3, rootY, D / 2))
    const canal = this.project(new Vector3(-W / 2 + 0.8, -0.2, -D / 2 - 0.6))
    return {
      pond: { ...pond, visible: pond.visible && this.water.visible },
      root: { ...root, visible: root.visible && c.rootM > 0.05 },
      canal,
      depth: DEPTH_MARKS.map((d) => this.project(new Vector3(-W / 2 - 0.25, -d * PX_M, D / 2))),
    }
  }
}

