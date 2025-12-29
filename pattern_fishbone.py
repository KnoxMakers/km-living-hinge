import math
import inkex


def generate_fishbone_pattern(
    *,
    polygons_rot,
    min_x: float,
    max_x: float,
    min_y: float,
    max_y: float,
    column_spacing: float,
    pattern_width: float,
    slot_length: float,
    slot_gap: float,
    stroke_style: dict,
    hinge_group: inkex.Group,
    rot_fn,
    point_in_polys,
    offset_factor: float,
):
    """Generate clipped V-shaped fishbone slots."""
    cell_h = slot_length + slot_gap
    if cell_h <= 0:
        raise inkex.AbortExtension("Fishbone gap results in non-positive step.")

    dx_base = pattern_width * 0.5
    x = min_x
    col_index = 0
    step_x = pattern_width + column_spacing
    if step_x <= 0:
        raise inkex.AbortExtension("Fishbone spacing results in non-positive step.")
    start_y = min_y - cell_h  # extend one row upward so staggered rows cover the top edge

    def _segment_intersections(p0, p1):
        x0, y0 = p0
        x1, y1 = p1
        ts = []
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
        return ts

    def _clip_segment(p0, p1):
        ts = [0.0, 1.0]
        ts.extend(_segment_intersections(p0, p1))
        ts = sorted(set(ts))
        segs = []
        for i in range(len(ts) - 1):
            t0, t1 = ts[i], ts[i + 1]
            if t1 - t0 < 1e-6:
                continue
            mid_t = (t0 + t1) * 0.5
            mid_pt = (p0[0] + (p1[0] - p0[0]) * mid_t, p0[1] + (p1[1] - p0[1]) * mid_t)
            if point_in_polys(mid_pt):
                a = (p0[0] + (p1[0] - p0[0]) * t0, p0[1] + (p1[1] - p0[1]) * t0)
                b = (p0[0] + (p1[0] - p0[0]) * t1, p0[1] + (p1[1] - p0[1]) * t1)
                segs.append((a, b))
        return segs

    while x <= max_x + 0.001:
        y_offset = offset_factor if col_index % 2 == 1 else 0.0
        y = start_y + y_offset
        while y <= max_y + 0.001:
            apex_y = y
            base_y = y + slot_length  # full geometry; clipping trims to shape
            left_pt = (x - dx_base, base_y)
            apex_pt = (x, apex_y)
            right_pt = (x + dx_base, base_y)
            if any(point_in_polys(pt) for pt in (left_pt, apex_pt, right_pt)):
                leg1 = _clip_segment(left_pt, apex_pt)
                leg2 = _clip_segment(apex_pt, right_pt)
                segments = []
                if leg1:
                    segments.append(leg1[-1])  # last toward apex
                if leg2:
                    segments.append(leg2[0])  # first from apex
                if segments:
                    d_parts = []
                    for p_start, p_end in segments:
                        rs = rot_fn(p_start)
                        re = rot_fn(p_end)
                        d_parts.append(f"M {rs[0]},{rs[1]} L {re[0]},{re[1]}")
                    path = inkex.PathElement()
                    path.style = stroke_style
                    path.set("d", " ".join(d_parts))
                    hinge_group.add(path)
            y += cell_h
        col_index += 1
        x += step_x
