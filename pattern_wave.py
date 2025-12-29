import math
import inkex


def _clip_segments(polygons_rot, point_in_polys, p0, p1):
    x0, y0 = p0
    x1, y1 = p1
    ts = [0.0, 1.0]
    for poly in polygons_rot:
        for i in range(len(poly) - 1):
            x2, y2 = poly[i]
            x3, y3 = poly[i + 1]
            denom = (x1 - x0) * (y3 - y2) - (y1 - y0) * (x3 - x2)
            if math.isclose(denom, 0.0, abs_tol=1e-12):
                continue
            t = ((x2 - x0) * (y3 - y2) - (y2 - y0) * (x3 - x2)) / denom
            u = ((x2 - x0) * (y1 - y0) - (y2 - y0) * (x1 - x0)) / denom
            if -1e-9 <= t <= 1 + 1e-9 and -1e-9 <= u <= 1 + 1e-9:
                ts.append(max(0.0, min(1.0, t)))
    ts = sorted(set(ts))
    segs = []
    for i in range(len(ts) - 1):
        t0, t1 = ts[i], ts[i + 1]
        if t1 - t0 < 1e-6:
            continue
        mid_t = (t0 + t1) * 0.5
        mid_pt = (x0 + (x1 - x0) * mid_t, y0 + (y1 - y0) * mid_t)
        if point_in_polys(mid_pt):
            a = (x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0)
            b = (x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1)
            segs.append((a, b))
    return segs


def _sample_quadratic(p0, c, p1, steps=12):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        mt = 1 - t
        x = mt * mt * p0[0] + 2 * mt * t * c[0] + t * t * p1[0]
        y = mt * mt * p0[1] + 2 * mt * t * c[1] + t * t * p1[1]
        pts.append((x, y))
    return pts


def generate_wave_pattern(
    *,
    polygons_rot,
    min_x: float,
    max_x: float,
    min_y: float,
    max_y: float,
    cell_width: float,
    cell_height: float,
    gap: float,
    spacing: float,
    param_a: float,
    param_b: float,
    stroke_style: dict,
    hinge_group: inkex.Group,
    rot_fn,
    point_in_polys,
    offset_factor: float,
):
    cell_h = cell_height + gap
    cell_w = cell_width + spacing
    if cell_h <= 0 or cell_w <= 0:
        raise inkex.AbortExtension("Wave spacing/gap results in non-positive step.")

    start_x = min_x - cell_w
    start_y = min_y - cell_h

    x = start_x
    col_index = 0
    while x <= max_x + cell_w + 0.001:
        y_offset = offset_factor if col_index % 2 == 1 else 0.0
        y = start_y + y_offset
        while y <= max_y + cell_h + 0.001:
            min_cx, max_cx = x, x + cell_width
            min_cy, max_cy = y, y + cell_height

            def _clamp(pt):
                px, py = pt
                return (min(max(px, min_cx), max_cx), min(max(py, min_cy), max_cy))

            p0 = _clamp((x + 0.0 * cell_width, y + 0.0 * cell_height))
            p1 = _clamp((x + 0.25 * cell_width, y + 0.0 * cell_height))
            c1 = _clamp((x + 0.5 * cell_width + param_a * cell_width, y + 0.0 * cell_height + param_b * cell_height))
            mid = _clamp((x + 0.5 * cell_width, y + 0.5 * cell_height))
            c2 = _clamp((x + 0.5 * cell_width - param_a * cell_width, y + 1.0 * cell_height - param_b * cell_height))
            p2 = _clamp((x + 0.75 * cell_width, y + 1.0 * cell_height))
            p3 = _clamp((x + 1.0 * cell_width, y + 1.0 * cell_height))

            pts = (
                [p0, p1]
                + _sample_quadratic(p1, c1, mid)[1:]
                + _sample_quadratic(mid, c2, p2)[1:]
                + [p3]
            )

            clipped_segments = []
            for i in range(len(pts) - 1):
                segs = _clip_segments(polygons_rot, point_in_polys, pts[i], pts[i + 1])
                clipped_segments.extend(segs)

            if clipped_segments:
                d_parts = []
                for idx, (a, b) in enumerate(clipped_segments):
                    ra = rot_fn(a)
                    rb = rot_fn(b)
                    cmd = "M" if idx == 0 else "M"
                    d_parts.append(f"{cmd} {ra[0]},{ra[1]} L {rb[0]},{rb[1]}")
                path = inkex.PathElement()
                path.style = stroke_style
                path.set("d", " ".join(d_parts))
                hinge_group.add(path)

            y += cell_h
        col_index += 1
        x += cell_w
