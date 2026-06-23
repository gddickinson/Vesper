"""GPU renderer for the ICT-FaceKit head (moderngl).

Reuses faceView's ICT mesh + pose pipeline (``apply_blendshapes``) and per-
material colour palette (``_material_palette`` — our blue scheme), and rasterises
on the GPU with a small Phong/lambert shader. Returns an **RGBA** uint8 image
(transparent background, so an animated effect can show behind the head) — ~10x
faster than ``render_face``, so the ICT face runs at full frame rate.

Self-contained + lazy: a standalone moderngl context is created on first use
(on the calling thread). ``render`` returns ``None`` on any failure so the caller
falls back to the software renderer.
"""
from __future__ import annotations

import numpy as np

_VS = """
#version 330
in vec3 in_pos; in vec3 in_nrm; in vec3 in_col; in float in_emit;
out vec3 v_nrm; out vec3 v_col; out float v_emit; out vec3 v_pos;
void main() {
    gl_Position = vec4(in_pos, 1.0);
    v_nrm = in_nrm; v_col = in_col; v_emit = in_emit; v_pos = in_pos;
}
"""
_FS = """
#version 330
in vec3 v_nrm; in vec3 v_col; in float v_emit; in vec3 v_pos; out vec4 f;
uniform float u_time;
float h21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float starfield(vec2 uv, float t) {
    vec2 g = floor(uv), fp = fract(uv);
    float present = step(0.5, h21(g));             // ~50% of cells hold a star
    vec2 c = vec2(h21(g + 11.0), h21(g + 57.0));   // star position within cell
    float d = length(fp - c);
    float core = smoothstep(0.18, 0.0, d) + 0.6 * smoothstep(0.45, 0.0, d);
    float tw = 0.45 + 0.55 * sin(t * 1.8 + h21(g) * 6.2831);  // twinkle
    return present * core * max(0.05, tw);
}
void main() {
    vec3 N = normalize(v_nrm);
    float facing = abs(N.z);
    float d = max(0.0, dot(N, normalize(vec3(0.25, 0.4, 1.0))));
    float fres = pow(1.0 - facing, 2.2);
    vec3 skin = v_col * (0.55 + 0.55 * d) + v_col * fres * 1.3;
    // Starry-sky eyeballs: deep space + drifting, twinkling stars.
    vec2 uv = v_pos.xy * 52.0 + vec2(sin(u_time * 0.15) * 2.0,
                                     cos(u_time * 0.11) * 1.5);
    float s = starfield(uv, u_time)
            + 0.85 * starfield(uv * 1.9 + vec2(3.0, 7.0), u_time * 1.3);
    vec3 sky = vec3(0.03, 0.05, 0.13)
             + vec3(0.06, 0.03, 0.13) * (0.5 + 0.5 * sin(v_pos.y * 7.0
                                                          + u_time * 0.2));
    vec3 eye = sky + vec3(0.9, 0.95, 1.0) * clamp(s * 1.5, 0.0, 1.6);
    f = vec4(mix(skin, eye, clamp(v_emit, 0.0, 1.0)), 1.0);
}
"""

# Eyelash strands: fine glowing lines drawn from the lash line (the solid ribbon is
# hidden in the main pass). lin_a tapers each strand from root (bright) to tip (faint).
_LVS = """
#version 330
in vec3 lin_pos; in float lin_a; out float v_a;
void main() { gl_Position = vec4(lin_pos, 1.0); v_a = lin_a; }
"""
_LFS = """
#version 330
in float v_a; out vec4 f; uniform vec3 lcol; uniform float lalpha;
void main() { f = vec4(lcol, v_a * lalpha); }
"""

_S: dict = {}                                  # lazy singleton state


def available() -> bool:
    try:
        import moderngl  # noqa: F401
        from faceview.vision.ict_face import load_ict_model  # noqa: F401
        return True
    except Exception:
        return False


def _init(w, h):
    import moderngl
    from faceview.vision.ict_face import load_ict_model
    ctx = moderngl.create_context(standalone=True, require=330)
    ctx.enable(moderngl.DEPTH_TEST)
    prog = ctx.program(vertex_shader=_VS, fragment_shader=_FS)
    model = load_ict_model()
    tri = model.triangles.reshape(-1).astype(np.int64)          # (3M,)
    n3 = tri.size
    vbo = ctx.buffer(reserve=n3 * 12, dynamic=True)
    nbo = ctx.buffer(reserve=n3 * 12, dynamic=True)
    cbo = ctx.buffer(reserve=n3 * 12, dynamic=True)
    ebo = ctx.buffer(reserve=n3 * 4, dynamic=True)
    vao = ctx.vertex_array(prog, [(vbo, "3f", "in_pos"), (nbo, "3f", "in_nrm"),
                                  (cbo, "3f", "in_col"), (ebo, "1f", "in_emit")])
    # Vertex clusters for the left/right eyeball (so we can enlarge them).
    eb = {i for i, mm in enumerate(model.materials) if mm in _EYEBALL}
    emask = np.isin(model.tri_materials, list(eb)) if eb else None
    clusters = []
    if emask is not None and emask.any():
        ev = np.unique(model.triangles[emask].reshape(-1))
        cx = float(model.vertices[:, 0].mean())
        clusters = [ev[model.vertices[ev, 0] < cx], ev[model.vertices[ev, 0] >= cx]]
    # Lashes: hide the solid ribbon in the main pass; draw strands instead. The
    # ribbon's connected components are the per-lid segments (its lash lines).
    tm = np.asarray(model.tri_materials)
    lash_i = model.materials.index(_LASHES) if _LASHES in model.materials else -1
    lash_tri = tm == lash_i
    main_mask = ~lash_tri
    main_tri = model.triangles[main_mask].reshape(-1).astype(np.int64)
    lash_segments, lash_all = [], np.array([], np.int64)
    if lash_i >= 0 and lash_tri.any():
        lt = model.triangles[lash_tri]
        lash_all = np.unique(lt.reshape(-1))
        parent = {int(v): int(v) for v in lash_all}

        def _find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a
        for a, b, c2 in lt:
            ra, rb, rc = _find(int(a)), _find(int(b)), _find(int(c2))
            parent[rb] = ra
            parent[rc] = ra
        comp = {}
        for v in lash_all:
            comp.setdefault(_find(int(v)), []).append(int(v))
        lash_segments = [np.array(g, np.int64) for g in comp.values()]
    lprog = ctx.program(vertex_shader=_LVS, fragment_shader=_LFS)
    lvbo = ctx.buffer(reserve=8192 * 16, dynamic=True)
    lvao = ctx.vertex_array(lprog, [(lvbo, "3f 1f", "lin_pos", "lin_a")])
    _S.update(ctx=ctx, prog=prog, model=model, tri=tri, main_tri=main_tri,
              main_mask=main_mask, vbo=vbo, nbo=nbo, cbo=cbo, ebo=ebo, vao=vao,
              eye_clusters=clusters, lash_segments=lash_segments, lash_all=lash_all,
              lprog=lprog, lvbo=lvbo, lvao=lvao,
              fbo=None, fbo_size=None, moderngl=moderngl)


def _ensure_fbo(w, h):
    ctx = _S["ctx"]
    if _S.get("fbo_size") == (w, h):
        return _S["fbo"]
    if _S.get("fbo") is not None:
        _S["fbo"].release()
        _S["ctex"].release()
        _S["dbuf"].release()
    ctex = ctx.texture((w, h), 4)               # RGBA: transparent background
    dbuf = ctx.depth_renderbuffer((w, h))
    fbo = ctx.framebuffer(color_attachments=[ctex], depth_attachment=dbuf)
    _S.update(fbo=fbo, ctex=ctex, dbuf=dbuf, fbo_size=(w, h))
    return fbo


def _pose(params):
    from faceview.vision.anatomy import face_params_to_au_values
    from faceview.vision.arkit_blendshapes import au_to_arkit_values
    from faceview.vision.ict_face import apply_blendshapes
    model = _S["model"]
    iw = {k: float(v) for k, v in (getattr(params, "identity_weights", {}) or {})
          .items() if isinstance(v, (int, float))}
    base = apply_blendshapes(model, iw) if iw else None        # identity (young)
    coefs = au_to_arkit_values(face_params_to_au_values(params))
    out = apply_blendshapes(model, coefs, base=base)           # + expression
    for idx in _S.get("eye_clusters", []):                     # enlarge eyeballs
        if idx.size:
            c = out[idx].mean(axis=0)
            out[idx] = c + (out[idx] - c) * EYE_SCALE
    return out


# Eyeball materials are a separate mesh; the lambert shader can't reproduce the
# xray eye glow, so override to natural colours (pale sclera, blue iris) that suit
# the blue avatar. They also fade with eye_open so a closed lid shows no eye.
_EYEBALL = {"M_ScleraLeft", "M_ScleraRight", "M_IrisLeft", "M_IrisRight",
            "M_LacrimalFluid"}
_EYE_COLOR = {
    "M_ScleraLeft": (0.0, 0.0, 0.0), "M_ScleraRight": (0.0, 0.0, 0.0),
    "M_IrisLeft": (0.0, 0.0, 0.0), "M_IrisRight": (0.0, 0.0, 0.0),
    "M_LacrimalFluid": (0.0, 0.0, 0.0),       # entirely black eyeballs
}
# Socket lining + lashes. The occlusion ring used to read as a dark shadow around
# the eye — colour it to the eyelid skin so it disappears; keep lashes a faint hint.
_OCCLUSION = "M_EyeOcclusion"
_LASHES = "M_EyeLashes"
# Enlarge the eyeball a little (in the facing plane) so the eyes read bigger.
EYE_SCALE = np.array([1.22, 1.22, 1.0], dtype="f4")


def _color_emit(params):
    """Per-triangle (colour, emissive). Eyes use natural colours + are emissive
    (self-lit) when open, and blend to the eyelid skin (+ emissive 0) as they
    close, so a shut lid shows neither a black nor a bright eyeball."""
    from faceview.vision.ict_face import _material_palette
    model = _S["model"]
    pal = _material_palette(params)
    default = pal.get("M_Face", (0.5, 0.5, 0.5))
    eye_open = max(0.0, min(1.0, float(getattr(params, "eye_open", 1.0))))
    fade = max(0.0, min(1.0, (eye_open - 0.15) / 0.45))
    lid = pal.get("M_EyeBlend", pal.get("M_Face", default))
    skin = pal.get("M_Face", default)
    cols, emit = [], []
    for m in model.materials:
        if m in _EYEBALL:
            n = _EYE_COLOR[m]
            cols.append(tuple(lid[i] + (n[i] - lid[i]) * fade for i in range(3)))
            emit.append((0.35 if m == "M_LacrimalFluid" else 1.0) * fade)
        elif m == _OCCLUSION:                       # no shadow ring: match the lid
            cols.append(tuple(lid[i] * 1.08 for i in range(3)))
            emit.append(0.0)
        elif m == _LASHES:                          # a faint lash hint, not a hole
            cols.append(tuple(skin[i] * 0.9 for i in range(3)))
            emit.append(0.0)
        else:
            cols.append(pal.get(m, default))
            emit.append(0.0)
    if not cols:
        cols, emit = [default], [0.0]
    tm = model.tri_materials
    return np.array(cols, "f4")[tm], np.array(emit, "f4")[tm]


def _interp_edge(a, p, x):
    """Point on an edge polyline (points ``p`` sorted by the scalar ``a``) at ``x``."""
    if x <= a[0]:
        return p[0]
    if x >= a[-1]:
        return p[-1]
    i = int(np.searchsorted(a, x))
    a0, a1 = float(a[i - 1]), float(a[i])
    w = (x - a0) / (a1 - a0 + 1e-12)
    return p[i - 1] * (1.0 - w) + p[i] * w


def _lash_lines(vr):
    """Lash strands that sit ON the eyelid rim and curl outward (in rotated `vr`).

    The lash ribbon is a thin strip with two long edges: a **root edge** on the lid
    margin (nearer the eyeball) and a free **tip edge**. Per lid segment we PCA out a
    *length* axis (along the lash line) and a *width* axis (root↔tip), split the verts
    into the two edges, and pick the root edge as the one nearer the eyeball. Strand
    roots are taken straight from the root-edge vertices — so they follow the lid
    curve — and each grows toward its paired tip (interpolated at the same position
    along the line) with a gentle outward curl, tapering bright root → faint tip.
    Built from the *posed* verts each frame, so the lashes deform and blink."""
    segs = _S.get("lash_segments")
    if not segs:
        return None
    eye_centers = [vr[c].mean(0) for c in _S.get("eye_clusters", []) if c.size]
    if not eye_centers:                                 # no eyeball mesh: split by x
        av = vr[_S["lash_all"]]
        mx = float(av[:, 0].mean())
        lo_v, hi_v = av[av[:, 0] < mx], av[av[:, 0] >= mx]
        eye_centers = [lo_v.mean(0) if lo_v.size else av.mean(0),
                       hi_v.mean(0) if hi_v.size else av.mean(0)]
    M = 5                                                # points per curved strand
    pts, alpha = [], []
    for seg in segs:
        P = vr[seg]
        if len(P) < 6:
            continue
        X = P - P.mean(0)
        try:
            _u, sv, vt = np.linalg.svd(X, full_matrices=False)
        except Exception:
            continue
        if sv[0] < 2.2 * (sv[1] + 1e-9):                # blob (e.g. inner corner):
            continue                                    # no clean lash line -> skip
        a_proj, w_proj = X @ vt[0], X @ vt[1]           # along-line, across-width
        lo_m = w_proj < float(np.median(w_proj))
        hi_m = ~lo_m
        if lo_m.sum() < 2 or hi_m.sum() < 2:
            continue
        eye = min(eye_centers,
                  key=lambda e: float(((P.mean(0) - e)[:2] ** 2).sum()))
        # root edge = the long edge nearer the eyeball; the other is the free tip.
        if (((P[lo_m].mean(0) - eye) ** 2).sum()
                <= ((P[hi_m].mean(0) - eye) ** 2).sum()):
            root_m, tip_m = lo_m, hi_m
        else:
            root_m, tip_m = hi_m, lo_m
        oa = np.argsort(a_proj[root_m])
        ra, rp = a_proj[root_m][oa], P[root_m][oa]
        ob = np.argsort(a_proj[tip_m])
        ta, tp = a_proj[tip_m][ob], P[tip_m][ob]
        # only keep roots inside the tip edge's span, so each strand pairs with a
        # real interpolated tip (no clamped, cross-eye strands at the segment ends).
        span = float(ta[-1] - ta[0])
        margin = 0.06 * span
        keep = (ra >= ta[0] - margin) & (ra <= ta[-1] + margin)
        ra, rp = ra[keep], rp[keep]
        if len(rp) < 2:
            continue
        if len(rp) > 16:                                # bound strand count / segment
            idx = np.linspace(0, len(rp) - 1, 16).round().astype(int)
            ra, rp = ra[idx], rp[idx]
        a0_lo, a_span = float(ra[0]), float(ra[-1] - ra[0]) + 1e-9
        for a0, root in zip(ra, rp):
            tip = _interp_edge(ta, tp, float(a0))       # paired point on the tip edge
            grow = tip - root
            glen = float(np.linalg.norm(grow)) + 1e-9
            gdir = grow / glen                          # ribbon's own growth direction
            out = root - eye                            # outward, in the view plane
            out[2] = 0.0
            # curl perpendicular to growth, bowing to the side away from the eye
            perp = np.array([-gdir[1], gdir[0]], "f8")
            if perp @ out[:2] < 0:
                perp = -perp
            perp /= (np.hypot(perp[0], perp[1]) + 1e-9)
            # longest mid-lid, shortest at the corners (the segment ends)
            f = (float(a0) - a0_lo) / a_span
            taper = 0.45 + 0.55 * np.sin(np.pi * f)
            ln = glen * 1.02 * taper                    # a touch shorter overall
            end = root + gdir * ln
            mid = (root + end) * 0.5
            ctrl = mid.copy()
            ctrl[0] += perp[0] * ln * 0.27
            ctrl[1] += perp[1] * ln * 0.27
            prev = root
            for j in range(1, M):
                u = j / (M - 1)
                q = ((1 - u) ** 2) * root + 2 * (1 - u) * u * ctrl + (u ** 2) * end
                pts.append(prev)
                pts.append(q)
                alpha.append(0.92 * (1.0 - (j - 1) / (M - 1)) + 0.05)
                alpha.append(0.92 * (1.0 - j / (M - 1)) + 0.05)
                prev = q
    if not pts:
        return None
    if len(pts) > 8000:                                 # buffer safety (8192 cap)
        pts, alpha = pts[:8000], alpha[:8000]
    return np.asarray(pts, "f4"), np.asarray(alpha, "f4")


def render(params, size):
    w, h = int(size[0]), int(size[1])
    if w < 2 or h < 2:
        return None
    try:
        if not _S:
            _init(w, h)
        ctx = _S["ctx"]
        main_tri, main_mask = _S["main_tri"], _S["main_mask"]
        verts = _pose(params).astype("f4")
        c = (verts.min(0) + verts.max(0)) / 2.0
        vc = verts - c
        # head nod / turn (base yaw pi so the FACE faces the camera, not the back)
        py = float(getattr(params, "pitch", 0.0)) * 0.4
        yw = np.pi + float(getattr(params, "yaw", 0.0)) * 0.6
        cy, sy, cp, sp = np.cos(yw), np.sin(yw), np.cos(py), np.sin(py)
        Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], "f4")
        Rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]], "f4")
        vr = vc @ (Ry @ Rx).T
        # per-triangle flat normals (in rotated space, projection-independent)
        t = _S["model"].triangles
        e1 = vr[t[:, 1]] - vr[t[:, 0]]
        e2 = vr[t[:, 2]] - vr[t[:, 0]]
        nrm = np.cross(e1, e2)
        nrm /= (np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-8)
        # fit to NDC (aspect-correct so the head isn't stretched)
        span = vr.max(0) - vr.min(0)
        aspect = h / w
        s = 1.72 / max(span[1], span[0] * aspect, 1e-6)
        p = vr * s
        p[:, 0] *= aspect
        zmin, zmax = float(p[:, 2].min()), float(p[:, 2].max())
        p[:, 2] = (p[:, 2] - zmin) / (zmax - zmin + 1e-6) * 1.8 - 0.9
        col_tri, emit_tri = _color_emit(params)        # per-triangle (all tris)
        flat_p = p[main_tri].astype("f4")               # main pass excludes lashes
        flat_n = np.repeat(nrm[main_mask], 3, axis=0).astype("f4")
        flat_c = np.repeat(col_tri[main_mask], 3, axis=0).astype("f4")
        flat_e = np.repeat(emit_tri[main_mask], 3, axis=0).astype("f4")
        _S["vbo"].write(np.ascontiguousarray(flat_p).tobytes())
        _S["nbo"].write(np.ascontiguousarray(flat_n).tobytes())
        _S["cbo"].write(np.ascontiguousarray(flat_c).tobytes())
        _S["ebo"].write(np.ascontiguousarray(flat_e).tobytes())
        fbo = _ensure_fbo(w, h)
        fbo.use()
        ctx.viewport = (0, 0, w, h)
        ctx.clear(0.0, 0.0, 0.0, 0.0)              # transparent: bg shows through
        mgl = _S["moderngl"]
        try:
            _S["prog"]["u_time"].value = float(getattr(params, "_t", 0.0)) % 1000.0
        except Exception:
            pass
        _S["vao"].render(mgl.TRIANGLES, vertices=main_tri.size)
        # eyelash strands: fine glowing lines on top (no depth, alpha-blended)
        ll = _lash_lines(vr)
        if ll is not None:
            lp, la = ll
            cp = lp * s
            cp[:, 0] *= aspect
            cp[:, 2] = (cp[:, 2] - zmin) / (zmax - zmin + 1e-6) * 1.8 - 0.9
            lin = np.concatenate([cp, la.reshape(-1, 1)], axis=1).astype("f4")
            _S["lvbo"].write(np.ascontiguousarray(lin).tobytes())
            eo = max(0.0, min(1.0, float(getattr(params, "eye_open", 1.0))))
            try:
                _S["lprog"]["lcol"].value = (0.55, 0.85, 0.97)
                _S["lprog"]["lalpha"].value = 0.6 * max(0.12, eo)
            except Exception:
                pass
            ctx.disable(mgl.DEPTH_TEST)
            ctx.blend_func = (mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA)
            ctx.enable(mgl.BLEND)
            _S["lvao"].render(mgl.LINES, vertices=cp.shape[0])
            ctx.disable(mgl.BLEND)
            ctx.enable(mgl.DEPTH_TEST)
        buf = fbo.read(components=4)
        rgba = np.flipud(np.frombuffer(buf, "u1").reshape(h, w, 4))
        return np.ascontiguousarray(rgba)                       # -> RGBA
    except Exception:
        _S.clear()
        return None
