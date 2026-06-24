"""GLSL for the GPU face: a vertex shader (with point-size for the dot-matrix
render mode) and a fragment shader that switches between cyberpunk **eye
patterns** and **skin treatments** by uniform, plus a fresnel **ghost** alpha for
the translucent mode. The lash line shaders are unchanged.

Eye id 0 (starfield) and skin id 0 (smooth) reproduce the classic look exactly,
so the "Default" style is pixel-identical to before. The ids match
:mod:`vesper.face_styles`.
"""
from __future__ import annotations

VS = """
#version 330
in vec3 in_pos; in vec3 in_nrm; in vec3 in_col; in float in_emit;
uniform float u_pt;                       // point size (dot-matrix mode)
out vec3 v_nrm; out vec3 v_col; out float v_emit; out vec3 v_pos;
void main() {
    gl_Position = vec4(in_pos, 1.0);
    gl_PointSize = u_pt;
    v_nrm = in_nrm; v_col = in_col; v_emit = in_emit; v_pos = in_pos;
}
"""

FS = """
#version 330
in vec3 v_nrm; in vec3 v_col; in float v_emit; in vec3 v_pos; out vec4 f;
uniform float u_time;
uniform int u_eye;        // eye-pattern id
uniform int u_skin;       // skin-treatment id
uniform int u_ghost;      // 1 = translucent (fresnel alpha)
uniform vec3 u_acc;       // accent colour
uniform vec2 u_eyeL;      // left/right eyeball centres (NDC) + radius, for
uniform vec2 u_eyeR;      // eye-local polar patterns
uniform float u_eyer;

float h21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vn(vec2 p) {
    vec2 i = floor(p), fp = fract(p); fp = fp * fp * (3.0 - 2.0 * fp);
    float a = h21(i), b = h21(i + vec2(1, 0));
    float c = h21(i + vec2(0, 1)), d = h21(i + vec2(1, 1));
    return mix(mix(a, b, fp.x), mix(c, d, fp.x), fp.y);
}
float fbm(vec2 p) {
    float s = 0.0, a = 0.5;
    for (int i = 0; i < 5; i++) { s += a * vn(p); p *= 2.0; a *= 0.5; }
    return s;
}
float starfield(vec2 uv, float t) {
    vec2 g = floor(uv), fp = fract(uv);
    float present = step(0.5, h21(g));
    vec2 c = vec2(h21(g + 11.0), h21(g + 57.0));
    float d = length(fp - c);
    float core = smoothstep(0.18, 0.0, d) + 0.6 * smoothstep(0.45, 0.0, d);
    float tw = 0.45 + 0.55 * sin(t * 1.8 + h21(g) * 6.2831);
    return present * core * max(0.05, tw);
}

vec3 eye_pattern(int id, vec2 gp, vec2 lp, float t, vec3 acc) {
    // id 0: the classic starfield (kept byte-for-byte).
    if (id == 0) {
        vec2 uv = gp * 52.0 + vec2(sin(t * 0.15) * 2.0, cos(t * 0.11) * 1.5);
        float s = starfield(uv, t) + 0.85 * starfield(uv * 1.9 + vec2(3.0, 7.0), t * 1.3);
        vec3 sky = vec3(0.03, 0.05, 0.13)
                 + vec3(0.06, 0.03, 0.13) * (0.5 + 0.5 * sin(gp.y * 7.0 + t * 0.2));
        return sky + vec3(0.9, 0.95, 1.0) * clamp(s * 1.5, 0.0, 1.6);
    }
    float r = length(lp);
    float ang = atan(lp.y, lp.x);
    if (id == 1) {                                   // NEBULA
        float n = fbm(lp * 2.6 + vec2(t * 0.08, 0.0));
        float n2 = fbm(lp * 5.5 - vec2(0.0, t * 0.06));
        vec3 col = mix(vec3(0.03, 0.02, 0.10), acc * 1.1, n) + acc * 0.5 * n2 * n2;
        float s = starfield(gp * 60.0, t);
        return col + vec3(1.0) * clamp(s, 0.0, 1.0) * 0.9;
    }
    if (id == 2) {                                   // PLASMA
        float v = sin(lp.x * 9.0 + t * 1.3) + sin(lp.y * 11.0 - t * 1.1)
                + sin((lp.x + lp.y) * 8.0 + t) + sin(r * 16.0 - t * 2.0);
        v *= 0.25;
        vec3 rb = 0.5 + 0.5 * cos(6.2831 * (v + vec3(0.0, 0.33, 0.67)));
        return mix(acc, rb, 0.55) * (0.55 + 0.7 * abs(v)) + acc * 0.15;
    }
    if (id == 3) {                                   // CIRCUIT / HUD reticle
        float rings = smoothstep(0.08, 0.0, abs(fract(r * 5.0 - t * 0.25) - 0.5) - 0.40);
        float ticks = step(0.86, sin(ang * 16.0)) * step(0.45, r) * step(r, 1.05);
        float sweep = smoothstep(0.5, 0.0, abs(mod(ang - t * 1.6, 6.2831) - 3.14159));
        float core = smoothstep(0.34, 0.30, r);
        float g = clamp(rings + ticks * 0.7 + sweep * 0.5 + core * 0.5, 0.0, 1.4);
        return vec3(0.015, 0.04, 0.06) + acc * g;
    }
    if (id == 4) {                                   // MATRIX rain
        float col_i = floor(lp.x * 9.0);
        float sp = 0.5 + 0.7 * h21(vec2(col_i, 1.0));
        float yy = fract(lp.y * 0.5 + 0.5 + t * sp * 0.25 + h21(vec2(col_i, 3.0)));
        float head = smoothstep(0.0, 0.12, yy) * smoothstep(0.55, 0.12, yy);
        float gl = step(0.55, h21(floor(vec2(lp.x * 9.0, lp.y * 16.0 + t * sp * 4.0))));
        return acc * (head * 1.4 + gl * 0.4) * smoothstep(1.25, 0.6, r);
    }
    if (id == 5) {                                   // SOLAR corona
        float turb = fbm(lp * 4.0 + vec2(t * 0.2, ang));
        float core = smoothstep(0.7, 0.0, r);
        float flare = 0.5 + 0.5 * sin(ang * 9.0 + t * 1.5 + turb * 6.0);
        vec3 hot = mix(acc, vec3(1.0, 0.95, 0.7), core);
        return hot * (core + 0.6 * flare * smoothstep(1.1, 0.2, r)) + acc * turb * 0.3;
    }
    if (id == 6) {                                   // VOID + accretion ring
        float pulse = 0.5 + 0.5 * sin(t * 0.9);
        float ring = smoothstep(0.10, 0.0, abs(r - (0.45 + 0.05 * pulse)));
        float disk = smoothstep(1.1, 0.5, r) * (0.3 + 0.5 * fbm(vec2(ang * 2.0, r * 4.0 - t)));
        float hole = smoothstep(0.42, 0.30, r);
        return (acc * ring * 1.4 + acc * 0.5 * disk) * (1.0 - hole);
    }
    if (id == 7) {                                   // IRIS aperture
        float blades = 0.5 + 0.5 * sin(ang * 6.0 + r * 3.0);
        float rim = smoothstep(0.06, 0.0, abs(r - 0.85));
        float metal = (0.25 + 0.55 * blades) * smoothstep(1.0, 0.35, r);
        float pupil = smoothstep(0.34, 0.26, r);
        vec3 col = mix(acc * 0.8, vec3(0.85, 0.9, 1.0), blades) * metal;
        return col * (1.0 - pupil) + acc * rim;
    }
    if (id == 8) {                                   // HOLO scanlines
        float sc = 0.55 + 0.45 * sin(gp.y * 240.0 - t * 6.0);
        float fl = 0.9 + 0.1 * sin(t * 18.0);
        float s = starfield(gp * 70.0, t) * 0.5;
        return (acc * (0.5 + 0.5 * smoothstep(1.2, 0.0, r)) * sc * fl)
               + vec3(0.9, 0.95, 1.0) * s;
    }
    // id 9: SONAR expanding rings
    float rings = 0.5 + 0.5 * sin(r * 20.0 - t * 3.0);
    float pulse = smoothstep(1.1, 0.0, r) * pow(rings, 3.0);
    return vec3(0.01, 0.03, 0.05) + acc * pulse * 1.3;
}

vec3 skin_shade(int id, vec3 base, float facing, float fres, float d,
                vec2 gp, float t, vec3 acc) {
    if (id == 0) return base * (0.55 + 0.55 * d) + base * fres * 1.3;   // SMOOTH
    if (id == 1) {                                   // CHROME
        float spec = pow(max(d, 0.0), 32.0);
        vec3 env = mix(base * 0.22, vec3(0.85, 0.92, 1.0), fres);
        return env + vec3(1.0) * spec + acc * fres * 0.4;
    }
    if (id == 2)                                     // NEON RIM
        return base * 0.32 + acc * pow(fres, 1.4) * 2.3 + base * d * 0.3;
    if (id == 3) {                                   // CIRCUIT traces
        vec2 q = gp * 26.0;
        float l = min(abs(fract(q.x) - 0.5), abs(fract(q.y) - 0.5));
        float trace = smoothstep(0.06, 0.0, l) * step(0.45, h21(floor(q)));
        float node = step(0.93, h21(floor(q) + 5.0)) * smoothstep(0.18, 0.0, l);
        return base * (0.4 + 0.4 * d) + acc * (trace + node * 1.5) * 1.1;
    }
    if (id == 4) {                                   // HOLO scanlines
        float sc = 0.6 + 0.4 * sin(gp.y * 170.0 - t * 4.0);
        float fl = 0.92 + 0.08 * sin(t * 16.0);
        return (base * 0.35 + acc * 0.5) * sc * fl + acc * fres * 0.7;
    }
    if (id == 5) {                                   // IRIDESCENT
        vec3 a = 0.5 + 0.5 * cos(6.2831 * (fres + vec3(0.0, 0.33, 0.67)));
        return base * 0.28 + mix(acc, a, 0.6) * (0.4 + 0.8 * fres) + d * base * 0.2;
    }
    if (id == 6) return base * 0.45 * d + acc * 0.05;        // MATTE dark
    // id 7: GRID / Tron
    vec2 q = gp * 15.0;
    float ln = min(abs(fract(q.x) - 0.5), abs(fract(q.y) - 0.5));
    float g = smoothstep(0.045, 0.0, ln);
    return base * 0.22 * d + acc * g * 1.0 + acc * fres * 0.5;
}

void main() {
    vec3 N = normalize(v_nrm);
    float facing = abs(N.z);
    float d = max(0.0, dot(N, normalize(vec3(0.25, 0.4, 1.0))));
    float fres = pow(1.0 - facing, 2.2);
    vec3 skin = skin_shade(u_skin, v_col, facing, fres, d, v_pos.xy, u_time, u_acc);
    // eye-local polar coords (centred on the nearer eyeball)
    vec2 cen = (distance(v_pos.xy, u_eyeL) < distance(v_pos.xy, u_eyeR))
               ? u_eyeL : u_eyeR;
    vec2 lp = (v_pos.xy - cen) / max(u_eyer, 1e-3);
    vec3 eye = eye_pattern(u_eye, v_pos.xy, lp, u_time, u_acc);
    float e = clamp(v_emit, 0.0, 1.0);
    vec3 col = mix(skin, eye, e);
    float a = 1.0;
    if (u_ghost == 1) {                              // translucent fresnel hologram
        a = clamp(0.34 + 0.62 * fres, 0.0, 1.0);     // glowing form, edges brightest
        a = mix(a, max(a, 0.95), e);                 // keep the eyes solid
    }
    f = vec4(col, a);
}
"""

LVS = """
#version 330
in vec3 lin_pos; in float lin_a; out float v_a;
void main() { gl_Position = vec4(lin_pos, 1.0); v_a = lin_a; }
"""

LFS = """
#version 330
in float v_a; out vec4 f; uniform vec3 lcol; uniform float lalpha;
void main() { f = vec4(lcol, v_a * lalpha); }
"""
