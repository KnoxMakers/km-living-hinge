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


def _emit_polyline(polygons_rot, point_in_polys, rot_fn, hinge_group, stroke_style, segments):
    clipped_segments = []
    for a, b in segments:
        clipped_segments.extend(_clip_segments(polygons_rot, point_in_polys, a, b))
    if not clipped_segments:
        return

    d_parts = []
    for idx, (c, d) in enumerate(clipped_segments):
        rc = rot_fn(c)
        rd = rot_fn(d)
        d_parts.append(f"M {rc[0]},{rc[1]} L {rd[0]},{rd[1]}")

    path = inkex.PathElement()
    path.style = stroke_style
    path.set("d", " ".join(d_parts))
    hinge_group.add(path)


def generate_fabric_pattern(
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
    stroke_style: dict,
    hinge_group: inkex.Group,
    rot_fn,
    point_in_polys,
    offset_factor: float,
):
    cell_h = cell_height + gap
    cell_w = cell_width + spacing
    if cell_h <= 0 or cell_w <= 0:
        raise inkex.AbortExtension("Fabric spacing/gap results in non-positive step.")

    start_x = min_x - cell_w
    start_y = min_y - cell_h

    x = start_x
    col_index = 0
    while x <= max_x + cell_w + 0.001:
        y_offset = offset_factor if col_index % 2 == 1 else 0.0
        y = start_y + y_offset
        while y <= max_y + cell_h + 0.001:
            # First polyline sequence
            segs1 = [
                ((x + 0.25 * cell_width, y + 0.25 * cell_height), (x + 0.0 * cell_width, y + 0.25 * cell_height)),
                ((x + 0.0 * cell_width, y + 0.25 * cell_height), (x + 0.0 * cell_width, y + 0.0 * cell_height)),
                ((x + 0.0 * cell_width, y + 0.0 * cell_height), (x + 0.5 * cell_width, y + 0.0 * cell_height)),
                ((x + 0.5 * cell_width, y + 0.0 * cell_height), (x + 0.5 * cell_width, y + 1.0 * cell_height)),
                ((x + 0.5 * cell_width, y + 1.0 * cell_height), (x + 1.0 * cell_width, y + 1.0 * cell_height)),
                ((x + 1.0 * cell_width, y + 1.0 * cell_height), (x + 1.0 * cell_width, y + 0.75 * cell_height)),
                ((x + 1.0 * cell_width, y + 0.75 * cell_height), (x + 0.75 * cell_width, y + 0.75 * cell_height)),
            ]

            # Second polyline sequence
            segs2 = [
                ((x + 0.75 * cell_width, y + 0.25 * cell_height), (x + 0.75 * cell_width, y + 0.0 * cell_height)),
                ((x + 0.75 * cell_width, y + 0.0 * cell_height), (x + 1.0 * cell_width, y + 0.0 * cell_height)),
                ((x + 1.0 * cell_width, y + 0.0 * cell_height), (x + 1.0 * cell_width, y + 0.5 * cell_height)),
                ((x + 1.0 * cell_width, y + 0.5 * cell_height), (x + 0.0 * cell_width, y + 0.5 * cell_height)),
                ((x + 0.0 * cell_width, y + 0.5 * cell_height), (x + 0.0 * cell_width, y + 1.0 * cell_height)),
                ((x + 0.0 * cell_width, y + 1.0 * cell_height), (x + 0.25 * cell_width, y + 1.0 * cell_height)),
                ((x + 0.25 * cell_width, y + 1.0 * cell_height), (x + 0.25 * cell_width, y + 0.75 * cell_height)),
            ]

            _emit_polyline(polygons_rot, point_in_polys, rot_fn, hinge_group, stroke_style, segs1)
            _emit_polyline(polygons_rot, point_in_polys, rot_fn, hinge_group, stroke_style, segs2)

            y += cell_h
        col_index += 1
        x += cell_w
