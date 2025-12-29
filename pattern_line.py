"""Line pattern generator for KM Living Hinge."""

import math
import inkex


def generate_line_pattern(
    *,
    intervals_fn,
    min_x: float,
    max_x: float,
    min_y: float,
    max_y: float,
    column_spacing: float,
    slot_length: float,
    slot_gap: float,
    stroke_style: dict,
    hinge_group: inkex.Group,
    rot_fn,
    offset_factor: float,
):
    """Generate staggered vertical line slots clipped to the shape."""
    step = slot_length + slot_gap
    if step <= 0:
        raise inkex.AbortExtension("Line gap results in non-positive step.")

    col_step = abs(column_spacing)
    if col_step < 1e-9:
        raise inkex.AbortExtension("Line column spacing must be non-zero.")

    x = min_x
    col_index = 0

    while x <= max_x + 0.001:
        intervals = sorted(intervals_fn(x), key=lambda p: p[0])
        if not intervals:
            col_index += 1
            x += col_step
            continue

        offset = offset_factor if col_index % 2 == 1 else 0.0
        base_start = min_y + offset

        for (raw_y0, raw_y1) in intervals:
            y0 = max(raw_y0, min_y)
            y1 = min(raw_y1, max_y)
            if y1 - y0 <= 0.001:
                continue

            n0 = math.ceil((y0 - slot_length - base_start) / step)
            y = base_start + n0 * step

            while y < y1 + 0.001:
                seg_start = max(y, y0)
                seg_end = min(y + slot_length, y1)
                if seg_end - seg_start > 0.001:
                    x0, y0r = rot_fn((x, seg_start))
                    x1, y1r = rot_fn((x, seg_end))
                    path = inkex.PathElement()
                    path.style = stroke_style
                    path.set("d", f"M {x0},{y0r} L {x1},{y1r}")
                    hinge_group.add(path)
                y += step

        col_index += 1
        x += col_step
