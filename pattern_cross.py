import math
import inkex


def generate_cross_pattern(
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
    """Generate cross pattern (inspired by Meerk40t set_cross) clipped to the shape."""
    cell_h = cell_height + gap
    cell_w = cell_width + spacing
    if cell_h <= 0 or cell_w <= 0:
        raise inkex.AbortExtension("Cross spacing/gap results in non-positive step.")

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

    start_x = min_x - cell_w  # extend one cell to reduce chances of skipped rows/cols at edges
    start_y = min_y - cell_h
    row_index = 0

    y = start_y
    while y <= max_y + cell_h + 0.001:
        x_offset = offset_factor if row_index % 2 == 1 else 0.0
        x = start_x + x_offset
        while x <= max_x + cell_w + 0.001:
            dx = cell_width * 0.1
            dy = 0.0  # allow arms to reach full height
            y_top = y
            y_mid = y + 0.5 * cell_height
            y_bot = y + cell_height
            # Points based on normalized set_cross pattern, spanning full height
            p1 = (x, y_top + dy)
            p2 = (x + 0.25 * cell_width + dx, y_mid)
            p3 = (x, y_bot - dy)

            p4 = (x + 0.25 * cell_width + dx, y_mid)
            p5 = (x + 0.75 * cell_width - dx, y_mid)

            p6 = (x + cell_width, y_top + dy)
            p7 = (x + 0.75 * cell_width - dx, y_mid)
            p8 = (x + cell_width, y_bot - dy)
            segments = [
                (p1, p2),
                (p2, p3),
                (p4, p5),
                (p6, p7),
                (p7, p8),
            ]

            for seg in segments:
                clipped = _clip_segment(*seg)
                for a, b in clipped:
                    ra = rot_fn(a)
                    rb = rot_fn(b)
                    path = inkex.PathElement()
                    path.style = stroke_style
                    path.set("d", f"M {ra[0]},{ra[1]} L {rb[0]},{rb[1]}")
                    hinge_group.add(path)

            x += cell_w
        row_index += 1
        y += cell_h
