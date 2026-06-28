//  Shaders.metal
//  Vesper — GPU shaders for the breathing visuals. Compiled into the app's
//  default.metallib (a .metal file in a file-system-synchronized group is built
//  automatically) and invoked from SwiftUI via `.colorEffect(ShaderLibrary.…)`.
//
//  `breathingOrb` renders a soft, fluid, self-lit orb whose core swells with the
//  breath `vol` and whose surface gently churns — a big step up from flat radial
//  gradients, at ~free GPU cost and 120 fps on ProMotion.

#include <metal_stdlib>
using namespace metal;

// --- cheap value noise ---------------------------------------------------
static float hash21(float2 p) {
    p = fract(p * float2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

static float vnoise(float2 p) {
    float2 i = floor(p);
    float2 f = fract(p);
    float a = hash21(i);
    float b = hash21(i + float2(1.0, 0.0));
    float c = hash21(i + float2(0.0, 1.0));
    float d = hash21(i + float2(1.0, 1.0));
    float2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

static float fbm(float2 p) {
    float v = 0.0, a = 0.5;
    for (int i = 0; i < 4; i++) { v += a * vnoise(p); p *= 2.0; a *= 0.5; }
    return v;
}

// --- the breathing orb ---------------------------------------------------
// Args (after the implicit position+color): view size, time, breath volume
// (0..1), and the tint colour. Returns premultiplied RGBA so it composites
// cleanly over whatever backdrop is below.
[[ stitchable ]]
half4 breathingOrb(float2 pos, half4 color,
                   float2 size, float t, float vol, half4 tint) {
    float2 c = size * 0.5;
    float maxR = min(size.x, size.y) * 0.5;
    float2 d = (pos - c) / maxR;                 // -1..1 across the smaller axis
    float r = length(d);

    // domain-warped turbulence for a living, fluid surface
    float turb = fbm(d * 2.6 + float2(t * 0.05, -t * 0.04));
    float coreR = 0.20 + 0.34 * vol;             // core grows as the lungs fill
    float surf  = coreR + 0.05 * turb * (0.5 + vol);

    // soft core: 1 inside, fading to 0 just past the wobbly surface
    float core = smoothstep(surf + 0.20, surf * 0.25, r);
    // outer halo glow
    float glow = exp(-r * 2.3) * (0.45 + 0.55 * vol);
    float a = clamp(core * 0.92 + glow * 0.45, 0.0, 1.0);

    float3 base = float3(tint.rgb);
    // brighter, slightly cooler core; warmer rim from the glow
    float3 rgb = base * (0.55 + 0.85 * core) + base * glow * 0.35;
    rgb += 0.035 * sin(t * 0.8 + r * 7.0);       // faint shimmer
    rgb += 0.05 * core * (turb - 0.5);           // subtle internal mottling

    return half4(half3(rgb * a), half(a));        // premultiplied
}

// =========================================================================
// Backdrop scenes. Each paints sparse, mostly-transparent features over the
// app's dark background (premultiplied RGBA), so the breath orb glows on top
// and there is no seam with Theme.bg. `off` is a CoreMotion parallax offset
// (points); zero on devices without motion (e.g. the simulator).
// =========================================================================

[[ stitchable ]]
half4 nightSkyScene(float2 pos, half4 color, float2 size, float t, float2 off) {
    float2 uv = pos / size;
    float3 pre = float3(0.0);
    float a = 0.0;

    // faint nebula haze, stronger toward the top
    float neb = fbm((pos + off * 0.6) * 0.006 + float2(t * 0.004, 0.0));
    float band = smoothstep(0.0, 0.75, 1.0 - uv.y);
    float3 nebCol = mix(float3(0.10, 0.12, 0.28), float3(0.22, 0.10, 0.30), neb);
    float nebA = neb * band * 0.18;
    pre += nebCol * nebA; a += nebA;

    // star field via grid hash (parallax-shifted)
    float2 sp = (pos + off * 1.6) / 14.0;
    float2 cell = floor(sp), f = fract(sp);
    float h = hash21(cell);
    if (h > 0.90) {
        float2 star = float2(hash21(cell + 1.3), hash21(cell + 2.7));
        float d = length(f - star);
        float tw = 0.5 + 0.5 * sin(t * (0.6 + h) + h * 10.0);
        float s = smoothstep(0.16, 0.0, d) * (0.45 + 0.55 * tw) * (1.0 - uv.y * 0.4);
        pre += float3(1.0) * s * 0.7; a += s * 0.7;
    }

    // soft moon, upper-right
    float2 m = float2(0.78, 0.20) * size;
    float moon = exp(-length(pos - m) * 0.02);
    pre += float3(0.92, 0.94, 1.0) * moon * 0.28; a += moon * 0.28;

    return half4(half3(pre), half(clamp(a, 0.0, 1.0)));
}

[[ stitchable ]]
half4 auroraScene(float2 pos, half4 color, float2 size, float t, float2 off) {
    float2 uv = (pos + off * 0.5) / size;
    float3 pre = float3(0.0);
    float a = 0.0;
    for (int i = 0; i < 3; i++) {
        float fi = float(i);
        float3 col = (i == 0) ? float3(0.2, 0.85, 0.6)
                   : (i == 1) ? float3(0.3, 0.55, 0.92)
                              : float3(0.5, 0.85, 0.5);
        float baseY = 0.20 + fi * 0.12;
        float wave = fbm(float2(uv.x * 3.0, t * (0.10 + 0.03 * fi) + fi));
        float curtain = exp(-pow((uv.y - baseY - 0.06 * wave) * 6.0, 2.0));
        float vert = 0.5 + 0.5 * sin(uv.x * 22.0 + t * 0.5 + wave * 6.0);
        float ca = curtain * (0.10 + 0.10 * vert);
        pre += col * ca; a += ca;
    }
    return half4(half3(pre), half(clamp(a, 0.0, 1.0)));
}

[[ stitchable ]]
half4 embersScene(float2 pos, half4 color, float2 size, float t, float2 off) {
    float2 uv = pos / size;
    float3 pre = float3(0.0);
    float a = 0.0;
    // faint warm base near the bottom
    float baseGlow = smoothstep(1.0, 0.5, uv.y) * 0.06;
    pre += float3(0.5, 0.2, 0.05) * baseGlow; a += baseGlow;
    // rising sparks (grid hash, scrolling upward)
    float2 g = (pos + off) / 22.0; g.y += t * 0.6;
    float2 cell = floor(g), f = fract(g);
    float h = hash21(cell);
    if (h > 0.82) {
        float2 sp = float2(hash21(cell + 3.1), hash21(cell + 7.7));
        float d = length(f - sp);
        float fade = sin(fract(h + t * 0.05) * 3.14159);
        float s = smoothstep(0.24, 0.0, d) * fade;
        pre += float3(1.0, 0.5 + 0.3 * h, 0.15) * s * 0.5; a += s * 0.5;
    }
    return half4(half3(pre), half(clamp(a, 0.0, 1.0)));
}

[[ stitchable ]]
half4 fireplaceScene(float2 pos, half4 color, float2 size, float t, float2 off) {
    float2 uv = pos / size;
    float3 pre = float3(0.0);
    float a = 0.0;
    float fl = fbm(float2(uv.x * 4.0, uv.y * 5.0 - t * 0.8));
    float glow = smoothstep(1.0, 0.25, uv.y);
    float flick = 0.6 + 0.7 * fl;
    float3 fire = mix(float3(0.85, 0.25, 0.05), float3(1.0, 0.65, 0.20), fl);
    float ga = glow * glow * flick * 0.26;
    pre += fire * ga; a += ga;
    // hearth core, bottom-centre
    float hd = length(pos - float2(0.5, 1.02) * size);
    float hearth = exp(-hd * 0.012);
    pre += float3(1.0, 0.6, 0.25) * hearth * 0.22; a += hearth * 0.22;
    return half4(half3(pre), half(clamp(a, 0.0, 1.0)));
}

[[ stitchable ]]
half4 oceanScene(float2 pos, half4 color, float2 size, float t, float2 off) {
    float2 uv = (pos + off * 0.3) / size;
    float3 pre = float3(0.0);
    float a = 0.0;
    float horizon = 0.46;
    if (uv.y > horizon) {
        float depth = (uv.y - horizon) / (1.0 - horizon);
        float w = sin(uv.y * 40.0 - t * 1.5 + sin(uv.x * 6.0 + t * 0.3) * 1.5);
        float lines = smoothstep(0.84, 1.0, w) * (0.3 + 0.7 * depth);
        float3 sea = mix(float3(0.05, 0.12, 0.22), float3(0.10, 0.20, 0.35), depth);
        float sa = 0.22 * depth + lines * 0.14;
        pre += sea * sa; a += sa;
        float glint = exp(-pow((uv.x - 0.5) * 8.0, 2.0)) * lines;
        pre += float3(0.8, 0.85, 1.0) * glint * 0.30; a += glint * 0.30;
    }
    float hg = exp(-pow((uv.y - horizon) * 20.0, 2.0));
    pre += float3(0.30, 0.35, 0.50) * hg * 0.15; a += hg * 0.15;
    return half4(half3(pre), half(clamp(a, 0.0, 1.0)));
}
