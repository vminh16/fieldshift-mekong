/**
 * Earth look: vivid land, deep navy ocean with sun glint, soft terminator,
 * cloud shadows, and a bright atmospheric rim on the lit (upper-right) limb.
 * All lighting is in view space so the sun stays fixed relative to the viewer
 * while the planet turns underneath it — like the reference render.
 */

const commonVertex = /* glsl */ `
  varying vec2 vUv;
  varying vec3 vN;
  varying vec3 vP;
  void main() {
    vUv = uv;
    vN = normalize(normalMatrix * normal);
    vec4 mv = modelViewMatrix * vec4(position, 1.0);
    vP = mv.xyz;
    gl_Position = projectionMatrix * mv;
  }
`

export const earthVertex = commonVertex

export const earthFragment = /* glsl */ `
  uniform sampler2D dayMap;
  uniform sampler2D maskMap;   // r = relief, g = land mask
  uniform sampler2D cloudMap;
  uniform vec3 sunDir;         // view space
  uniform float cloudOffset;
  uniform vec2 texel;          // 1 / mask texture size
  varying vec2 vUv;
  varying vec3 vN;
  varying vec3 vP;

  const vec3 HAZE = vec3(0.26, 0.54, 1.0);

  vec3 saturate3(vec3 c, float s) {
    float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
    return mix(vec3(l), c, s);
  }

  void main() {
    vec3 N = normalize(vN);
    vec3 V = normalize(-vP);
    vec3 L = normalize(sunDir);

    // Relief: perturb the normal with the bump channel (screen-space derivatives).
    float h  = texture2D(maskMap, vUv).r;
    float hx = texture2D(maskMap, vUv + vec2(texel.x, 0.0)).r - h;
    float hy = texture2D(maskMap, vUv + vec2(0.0, texel.y)).r - h;
    vec3 dpdx = dFdx(vP);
    vec3 dpdy = dFdy(vP);
    vec2 duvdx = dFdx(vUv);
    vec2 duvdy = dFdy(vUv);
    vec3 T = normalize(dpdx * duvdy.y - dpdy * duvdx.y);
    vec3 B = normalize(cross(N, T));
    N = normalize(N - (T * hx + B * hy) * 2.2);

    float land = smoothstep(0.3, 0.7, texture2D(maskMap, vUv).g);
    vec3 day = texture2D(dayMap, vUv).rgb;

    vec3 landCol = saturate3(day, 1.3) * vec3(0.95, 1.05, 0.9) * 1.08;
    // Deep navy ocean; keep a little of the source texture's variation.
    float dl = dot(day, vec3(0.2126, 0.7152, 0.0722));
    vec3 oceanCol = vec3(0.010, 0.042, 0.105) * (0.75 + 4.0 * dl);
    vec3 base = mix(oceanCol, landCol, land);

    float ndl = dot(N, L);
    float diff = smoothstep(-0.22, 0.75, ndl);

    // Cloud shadow, offset slightly away from the sun.
    float cs = texture2D(cloudMap, vUv + vec2(cloudOffset - 0.0012, 0.0010)).r;
    diff *= 1.0 - 0.42 * smoothstep(0.25, 0.85, cs);

    vec3 col = base * (0.035 + 1.18 * diff);

    // Ocean sun glint
    vec3 H = normalize(L + V);
    float spec = pow(max(dot(normalize(vN), H), 0.0), 140.0) * (1.0 - land);
    col += vec3(0.45, 0.62, 0.85) * spec * 0.4 * diff;
    // Broad, warm sun sheen on the ocean (right side of the disc, like the reference).
    float sheen = pow(max(dot(normalize(vN), H), 0.0), 10.0) * (1.0 - land);
    col += vec3(0.95, 0.88, 0.75) * sheen * 0.16 * diff;

    // Atmospheric scattering toward the limb, stronger on the day side.
    // Thin blue haze hugging the limb (not a white band).
    float fres = pow(1.0 - max(dot(normalize(vN), V), 0.0), 3.0);
    float dayside = smoothstep(-0.3, 0.6, dot(normalize(vN), L));
    col = mix(col, HAZE * (0.06 + 0.85 * dayside), fres * 0.55);

    gl_FragColor = vec4(col, 1.0);
    #include <colorspace_fragment>
  }
`

export const cloudVertex = commonVertex

export const cloudFragment = /* glsl */ `
  uniform sampler2D cloudMap;
  uniform vec3 sunDir;
  uniform float cloudOffset;
  varying vec2 vUv;
  varying vec3 vN;
  varying vec3 vP;
  void main() {
    vec3 N = normalize(vN);
    vec3 V = normalize(-vP);
    float c = texture2D(cloudMap, vUv + vec2(cloudOffset, 0.0)).r;
    float a = smoothstep(0.24, 0.92, c);
    float diff = smoothstep(-0.2, 0.7, dot(N, normalize(sunDir)));
    vec3 col = vec3(1.0, 1.0, 0.99) * (0.04 + 1.12 * diff);
    // Seen at a grazing angle, clouds sit behind more air: tint them blue and
    // let them thin out gradually so the limb never shows a hard white rim.
    float ndv = max(dot(N, V), 0.0);
    float fres = pow(1.0 - ndv, 3.0);
    col = mix(col, vec3(0.26, 0.54, 1.0) * (0.06 + 0.85 * diff), fres * 0.6);
    float edge = smoothstep(0.0, 0.45, ndv);
    gl_FragColor = vec4(col, a * 0.94 * edge);
    #include <colorspace_fragment>
  }
`

export const atmosphereVertex = /* glsl */ `
  varying vec3 vN;
  varying vec3 vP;
  void main() {
    vN = normalize(normalMatrix * normal);
    vec4 mv = modelViewMatrix * vec4(position, 1.0);
    vP = mv.xyz;
    gl_Position = projectionMatrix * mv;
  }
`

/**
 * Rendered on the back faces of a slightly larger sphere with ONE/ONE blending.
 * Alpha equals brightness, so where there is no glow the canvas stays fully
 * transparent (an alpha of 1 here used to paint a black ring over the page).
 */
export const atmosphereFragment = /* glsl */ `
  uniform vec3 sunDir;
  varying vec3 vN;
  varying vec3 vP;
  void main() {
    vec3 V = normalize(-vP);
    float rim = 1.0 - abs(dot(normalize(vN), V));
    // rim ≈ 0.80 at the planet's edge, 1.0 at the shell's edge.
    float t = clamp((rim - 0.80) / 0.20, 0.0, 1.0);
    float glow = pow(1.0 - t, 2.4) * smoothstep(0.0, 0.04, t + 0.02);
    vec2 nd = normalize(vN.xy + 1e-5);
    vec2 sd = normalize(sunDir.xy + 1e-5);
    float lit = smoothstep(-0.55, 0.75, dot(nd, sd));
    vec3 col = vec3(0.26, 0.54, 1.0) * glow * (0.025 + 0.95 * lit * lit);
    gl_FragColor = vec4(col, 1.0);
    #include <colorspace_fragment>
    // Alpha = brightness (after sRGB encoding) keeps colour premultiplied.
    gl_FragColor.a = clamp(max(gl_FragColor.r, max(gl_FragColor.g, gl_FragColor.b)), 0.0, 1.0);
  }
`
