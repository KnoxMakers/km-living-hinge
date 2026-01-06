# Living Hinge Engine
# - Takes a shape and fills a shape
# - Cuts off shapes at intersection points

import math
import inkex


def _sample_quadratic(p0, control, p1, steps=12):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        mt = 1 - t
        x = mt * mt * p0[0] + 2 * mt * t * control[0] + t * t * p1[0]
        y = mt * mt * p0[1] + 2 * mt * t * control[1] + t * t * p1[1]
        pts.append((x, y))
    return pts


def _sample_cubic(p0, c1, c2, p1, steps=12):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        mt = 1 - t
        x = (mt * mt * mt * p0[0] +
             3 * mt * mt * t * c1[0] +
             3 * mt * t * t * c2[0] +
             t * t * t * p1[0])
        y = (mt * mt * mt * p0[1] +
             3 * mt * mt * t * c1[1] +
             3 * mt * t * t * c2[1] +
             t * t * t * p1[1])
        pts.append((x, y))
    return pts


def _segment_intersections(p0, p1, polygons):
    x0, y0 = p0
    x1, y1 = p1
    ts = []
    for poly in polygons:
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


def _clip_segment(p0, p1, polygons, point_in_polys):
    x0, y0 = p0
    x1, y1 = p1
    ts = [0.0, 1.0]
    ts.extend(_segment_intersections(p0, p1, polygons))
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


def _point_in_poly(px, py, poly):
    inside = False
    n = len(poly)
    for i in range(n - 1):
        x1, y1 = poly[i]
        x2, y2 = poly[i + 1]
        if (y1 > py) != (y2 > py):
            x_int = (x2 - x1) * (py - y1) / (y2 - y1 + 1e-9) + x1
            if px < x_int:
                inside = not inside
    return inside


def _expand_shape_to_points(shape_data, offset_x, offset_y, width, height):
    polylines = []

    for segment in shape_data:
        if isinstance(segment, tuple) and len(segment) == 2 and isinstance(segment[0], str):
            seg_type, points = segment
            if seg_type == 'L':
                pts = [(p[0] + offset_x, p[1] + offset_y) for p in points]
                polylines.append(pts)
            elif seg_type == 'Q':
                p0 = (points[0][0] + offset_x, points[0][1] + offset_y)
                ctrl = (points[1][0] + offset_x, points[1][1] + offset_y)
                p1 = (points[2][0] + offset_x, points[2][1] + offset_y)
                pts = _sample_quadratic(p0, ctrl, p1)
                polylines.append(pts)
            elif seg_type == 'C':
                p0 = (points[0][0] + offset_x, points[0][1] + offset_y)
                c1 = (points[1][0] + offset_x, points[1][1] + offset_y)
                c2 = (points[2][0] + offset_x, points[2][1] + offset_y)
                p1 = (points[3][0] + offset_x, points[3][1] + offset_y)
                pts = _sample_cubic(p0, c1, c2, p1)
                polylines.append(pts)
        else:
            pts = [(p[0] + offset_x, p[1] + offset_y) for p in segment]
            polylines.append(pts)

    return polylines


def generate_hinge(
    polygons,
    shape_fn,
    height,
    width,
    x_spacing,
    y_spacing,
    y_offset,
    angle_rad=0.0,
    shape_kwargs=None,
):
    if not polygons:
        return []

    shape_kwargs = shape_kwargs or {}

    cell_width = width + x_spacing
    cell_height = height + y_spacing

    if cell_width <= 0 or cell_height <= 0:
        raise ValueError("Cell dimensions must be positive")

    all_x = [p[0] for poly in polygons for p in poly]
    all_y = [p[1] for poly in polygons for p in poly]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)

    cx = (min_x + max_x) / 2.0
    cy = (min_y + max_y) / 2.0

    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    def rotate_point(pt, cos_v, sin_v):
        x, y = pt
        dx = x - cx
        dy = y - cy
        return (
            cx + dx * cos_v - dy * sin_v,
            cy + dx * sin_v + dy * cos_v,
        )

    cos_neg = math.cos(-angle_rad)
    sin_neg = math.sin(-angle_rad)
    polygons_rot = [
        [rotate_point(p, cos_neg, sin_neg) for p in poly]
        for poly in polygons
    ]

    all_x = [p[0] for poly in polygons_rot for p in poly]
    all_y = [p[1] for poly in polygons_rot for p in poly]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)

    def point_in_polys(pt):
        for poly in polygons_rot:
            if _point_in_poly(pt[0], pt[1], poly):
                return True
        return False

    shape_data = shape_fn(height, width, **shape_kwargs)

    result_polylines = []

    start_x = min_x - cell_width
    start_y = min_y - cell_height

    x = start_x
    col_index = 0

    while x <= max_x + cell_width + 0.001:
        col_y_offset = y_offset if col_index % 2 == 1 else 0.0
        y = start_y + col_y_offset

        while y <= max_y + cell_height + 0.001:
            polylines = _expand_shape_to_points(shape_data, x, y, width, height)

            shape_segments = []
            for polyline in polylines:
                for i in range(len(polyline) - 1):
                    p0 = polyline[i]
                    p1 = polyline[i + 1]
                    clipped = _clip_segment(p0, p1, polygons_rot, point_in_polys)
                    for seg_start, seg_end in clipped:
                        ra = rotate_point(seg_start, cos_a, sin_a)
                        rb = rotate_point(seg_end, cos_a, sin_a)
                        shape_segments.append([ra, rb])
            if shape_segments:
                result_polylines.append(shape_segments)

            y += cell_height
        col_index += 1
        x += cell_width

    return result_polylines


def segments_to_svg_paths(polylines, stroke_style, group):
    for segments in polylines:
        if not segments:
            continue

        d_parts = []
        for segment in segments:
            if len(segment) < 2:
                continue
            d_parts.append(f"M {segment[0][0]},{segment[0][1]}")
            for pt in segment[1:]:
                d_parts.append(f"L {pt[0]},{pt[1]}")

        if d_parts:
            path = inkex.PathElement()
            path.style = stroke_style
            path.set("d", " ".join(d_parts))
            group.add(path)
