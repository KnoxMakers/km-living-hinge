#!/usr/bin/env python3
import math
import inkex
from inkex import bezier
from inkex.units import convert_unit
from pattern_line import generate_line_pattern
from pattern_fishbone import generate_fishbone_pattern
from pattern_cross import generate_cross_pattern
from pattern_bezier import generate_bezier_pattern
from pattern_wave import generate_wave_pattern
from pattern_fabric import generate_fabric_pattern


class KMLivingHinge(inkex.EffectExtension):
    def add_arguments(self, pars) -> None:
        pars.add_argument("--tab", default="line")
        pars.add_argument("--line_size_unit", default="mm")
        pars.add_argument("--line_angle_degrees", type=float, default=0.0)
        pars.add_argument("--line_column_spacing", type=float, default=1.0)
        pars.add_argument("--line_length", type=float, default=5.0)
        pars.add_argument("--line_gap", type=float, default=1.0)
        pars.add_argument("--line_offset", type=float, default=0.0)
        pars.add_argument("--fishbone_size_unit", default="mm")
        pars.add_argument("--fishbone_angle_degrees", type=float, default=0.0)
        pars.add_argument("--fishbone_column_spacing", type=float, default=1.0)
        pars.add_argument("--fishbone_width", type=float, default=3.0)
        pars.add_argument("--fishbone_height", type=float, default=5.0)
        pars.add_argument("--fishbone_gap", type=float, default=1.0)
        pars.add_argument("--fishbone_offset", type=float, default=0.0)
        pars.add_argument("--cross_size_unit", default="mm")
        pars.add_argument("--cross_angle_degrees", type=float, default=0.0)
        pars.add_argument("--cross_width", type=float, default=10.0)
        pars.add_argument("--cross_height", type=float, default=12.0)
        pars.add_argument("--cross_gap", type=float, default=-1.5)
        pars.add_argument("--cross_spacing", type=float, default=-0.5)
        pars.add_argument("--cross_offset", type=float, default=0.0)
        pars.add_argument("--bezier_size_unit", default="mm")
        pars.add_argument("--bezier_angle_degrees", type=float, default=0.0)
        pars.add_argument("--bezier_width", type=float, default=10.0)
        pars.add_argument("--bezier_height", type=float, default=12.0)
        pars.add_argument("--bezier_gap", type=float, default=-1.5)
        pars.add_argument("--bezier_spacing", type=float, default=-0.5)
        pars.add_argument("--bezier_tip", type=float, default=0.2)
        pars.add_argument("--bezier_center", type=float, default=0.3)
        pars.add_argument("--bezier_offset", type=float, default=0.0)
        pars.add_argument("--wave_size_unit", default="mm")
        pars.add_argument("--wave_angle_degrees", type=float, default=0.0)
        pars.add_argument("--wave_width", type=float, default=10.0)
        pars.add_argument("--wave_height", type=float, default=12.0)
        pars.add_argument("--wave_gap", type=float, default=-1.5)
        pars.add_argument("--wave_spacing", type=float, default=-0.5)
        pars.add_argument("--wave_a", type=float, default=0.0)
        pars.add_argument("--wave_b", type=float, default=0.0)
        pars.add_argument("--wave_offset", type=float, default=0.0)
        pars.add_argument("--fabric_size_unit", default="mm")
        pars.add_argument("--fabric_angle_degrees", type=float, default=0.0)
        pars.add_argument("--fabric_width", type=float, default=10.0)
        pars.add_argument("--fabric_height", type=float, default=12.0)
        pars.add_argument("--fabric_gap", type=float, default=-1.5)
        pars.add_argument("--fabric_spacing", type=float, default=-0.5)
        pars.add_argument("--fabric_offset", type=float, default=0.0)

    def _selection_bbox(self):
        selection = getattr(self.svg, "selection", None)
        if not selection:
            return None
        try:
            if len(selection) == 0:
                return None
        except TypeError:
            return None
        return selection.bounding_box()  # user units (px)

    def effect(self) -> None:
        opts = self.options
        pattern_type = opts.tab or "line"
        if pattern_type not in ("line", "fishbone", "cross", "bezier", "wave", "fabric"):
            pattern_type = "line"

        selection = getattr(self.svg, "selection", None)
        if not selection or len(selection) == 0:
            raise inkex.AbortExtension(
                "Select a shape (path, rectangle, circle, etc.); the hinge fills and is trimmed to your selection."
            )
        target = selection[0]
        bbox = target.bounding_box()
        path_elem = target.to_path_element()
        path = path_elem.path.transform(path_elem.composed_transform())
        csp = path.to_superpath()
        # Subdivide curves a bit to improve polygon approximation for inside tests
        bezier.cspsubdiv(csp, 0.25)

        # Determine angle based on active tab
        angle_deg = (
            opts.line_angle_degrees
            if pattern_type == "line"
            else opts.fishbone_angle_degrees
            if pattern_type == "fishbone"
            else opts.cross_angle_degrees
            if pattern_type == "cross"
            else opts.bezier_angle_degrees
            if pattern_type == "bezier"
            else opts.wave_angle_degrees
            if pattern_type == "wave"
            else opts.fabric_angle_degrees
        )
        angle_rad = math.radians(float(angle_deg))
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        cx = bbox.center_x
        cy = bbox.center_y

        def _uu(value, unit):
            return float(self.svg.unittouu(f"{value}{unit}"))

        def _rot(pt, cosv, sinv):
            x, y = pt
            dx = x - cx
            dy = y - cy
            return (
                cx + dx * cosv - dy * sinv,
                cy + dx * sinv + dy * cosv,
            )

        def _superpath_to_polygons(superpath):
            polys = []
            for sub in superpath:
                if not sub:
                    continue
                poly = []
                for node in sub:
                    if len(node) >= 2 and len(node[1]) == 2:
                        poly.append((node[1][0], node[1][1]))
                if len(poly) >= 3:
                    # ensure closed polygon for robustness
                    if poly[0] != poly[-1]:
                        poly.append(poly[0])
                    polys.append(poly)
            return polys

        polygons = _superpath_to_polygons(csp)
        polygons_rot = [[_rot(p, math.cos(-angle_rad), math.sin(-angle_rad)) for p in poly] for poly in polygons]

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

        def _point_in_polys(pt):
            for poly in polygons_rot:
                if _point_in_poly(pt[0], pt[1], poly):
                    return True
            return False

        def _intervals_at_x(x_pos: float):
            eps = 1e-9
            intervals = []
            for poly in polygons_rot:
                hits = []
                n = len(poly)
                for i in range(n - 1):
                    x1, y1 = poly[i]
                    x2, y2 = poly[i + 1]
                    if (x_pos < min(x1, x2) - eps) or (x_pos > max(x1, x2) + eps):
                        continue
                    if math.isclose(x1, x2, abs_tol=eps):
                        if math.isclose(x_pos, x1, abs_tol=eps):
                            hits.extend([y1, y2])
                        continue
                    t = (x_pos - x1) / (x2 - x1)
                    if -eps <= t <= 1 + eps:
                        y_hit = y1 + t * (y2 - y1)
                        hits.append(y_hit)
                hits.sort()
                dedup = []
                for y in hits:
                    if not dedup or abs(y - dedup[-1]) > 1e-6:
                        dedup.append(y)
                if len(dedup) % 2 == 1:
                    dedup = dedup[:-1]
                for i in range(0, len(dedup) - 1, 2):
                    y0 = dedup[i]
                    y1 = dedup[i + 1]
                    if y1 > y0 + eps:
                        intervals.append((y0, y1))
            return intervals

        # Bounds in rotated space
        all_x = [p[0] for poly in polygons_rot for p in poly]
        all_y = [p[1] for poly in polygons_rot for p in poly]
        origin_x = min(all_x)
        origin_y = min(all_y)
        hinge_width = max(all_x) - origin_x
        hinge_height = max(all_y) - origin_y

        padding = 0.0

        if pattern_type == "line":
            unit = opts.line_size_unit
            column_spacing = _uu(opts.line_column_spacing, unit)
            slot_length = _uu(opts.line_length, unit)
            slot_gap = _uu(opts.line_gap, unit)
            pattern_width = 0.0  # unused
            column_offset_factor = _uu(opts.line_offset, unit)
        elif pattern_type == "fishbone":
            unit = opts.fishbone_size_unit
            column_spacing = _uu(opts.fishbone_column_spacing, unit)
            slot_length = _uu(opts.fishbone_height, unit)
            slot_gap = _uu(opts.fishbone_gap, unit)
            pattern_width = _uu(opts.fishbone_width, unit)
            column_offset_factor = _uu(opts.fishbone_offset, unit)
        elif pattern_type == "cross":
            unit = opts.cross_size_unit
            column_spacing = _uu(opts.cross_spacing, unit)
            slot_length = _uu(opts.cross_height, unit)
            slot_gap = _uu(opts.cross_gap, unit)
            pattern_width = _uu(opts.cross_width, unit)
            column_offset_factor = _uu(opts.cross_offset, unit)
        elif pattern_type == "bezier":
            unit = opts.bezier_size_unit
            column_spacing = _uu(opts.bezier_spacing, unit)
            slot_length = _uu(opts.bezier_height, unit)
            slot_gap = _uu(opts.bezier_gap, unit)
            pattern_width = _uu(opts.bezier_width, unit)
            column_offset_factor = _uu(opts.bezier_offset, unit)
        elif pattern_type == "wave":
            unit = opts.wave_size_unit
            column_spacing = _uu(opts.wave_spacing, unit)
            slot_length = _uu(opts.wave_height, unit)
            slot_gap = _uu(opts.wave_gap, unit)
            pattern_width = _uu(opts.wave_width, unit)
            column_offset_factor = _uu(opts.wave_offset, unit)
        else:  # fabric
            unit = opts.fabric_size_unit
            column_spacing = _uu(opts.fabric_spacing, unit)
            slot_length = _uu(opts.fabric_height, unit)
            slot_gap = _uu(opts.fabric_gap, unit)
            pattern_width = _uu(opts.fabric_width, unit)
            column_offset_factor = _uu(opts.fabric_offset, unit)

        if slot_length <= 0:
            raise inkex.AbortExtension("Pattern height/length must be greater than zero.")
        if pattern_type == "cross" and math.isclose(pattern_width + column_spacing, 0.0, abs_tol=1e-6):
            raise inkex.AbortExtension("Cross spacing results in zero horizontal step.")

        stroke_width = float(self.svg.unittouu("0.1mm"))

        usable_width = hinge_width - 2 * padding
        usable_height = hinge_height - 2 * padding
        if usable_width <= 0 or usable_height <= 0:
            raise inkex.AbortExtension("Padding is too large for the hinge area.")

        min_x = origin_x + padding
        max_x = origin_x + hinge_width - padding
        min_y = origin_y + padding
        max_y = origin_y + hinge_height - padding

        parent = self.svg.get_current_layer()
        hinge_group = inkex.Group(id=self.svg.get_unique_id("km-living-hinge"))
        hinge_group.set("{http://www.inkscape.org/namespaces/inkscape}label", "KM Living Hinge")
        parent.add(hinge_group)

        stroke_style = {
            "stroke": "#000000",
            "stroke-width": str(stroke_width),
            "fill": "none",
            "stroke-linecap": "round",
        }

        rot_fn = lambda pt: _rot(pt, cos_a, sin_a)

        if pattern_type == "fishbone":
            generate_fishbone_pattern(
                polygons_rot=polygons_rot,
                min_x=min_x,
                max_x=max_x,
                min_y=min_y,
                max_y=max_y,
                column_spacing=column_spacing,
                pattern_width=pattern_width,
                slot_length=slot_length,
                slot_gap=slot_gap,
                stroke_style=stroke_style,
                hinge_group=hinge_group,
                rot_fn=rot_fn,
                offset_factor=column_offset_factor,
                point_in_polys=_point_in_polys,
            )
            return
        if pattern_type == "cross":
            generate_cross_pattern(
                polygons_rot=polygons_rot,
                min_x=min_x,
                max_x=max_x,
                min_y=min_y,
                max_y=max_y,
                cell_width=pattern_width,
                cell_height=slot_length,
                gap=slot_gap,
                spacing=column_spacing,
                stroke_style=stroke_style,
                hinge_group=hinge_group,
                rot_fn=rot_fn,
                offset_factor=column_offset_factor,
                point_in_polys=_point_in_polys,
            )
            return
        if pattern_type == "bezier":
            generate_bezier_pattern(
                polygons_rot=polygons_rot,
                min_x=min_x,
                max_x=max_x,
                min_y=min_y,
                max_y=max_y,
                cell_width=pattern_width,
                cell_height=slot_length,
                gap=slot_gap,
                spacing=column_spacing,
                anchor_tip=opts.bezier_tip,
                anchor_center=opts.bezier_center,
                stroke_style=stroke_style,
                hinge_group=hinge_group,
                rot_fn=rot_fn,
                offset_factor=column_offset_factor,
                point_in_polys=_point_in_polys,
            )
            return
        if pattern_type == "wave":
            generate_wave_pattern(
                polygons_rot=polygons_rot,
                min_x=min_x,
                max_x=max_x,
                min_y=min_y,
                max_y=max_y,
                cell_width=pattern_width,
                cell_height=slot_length,
                gap=slot_gap,
                spacing=column_spacing,
                param_a=opts.wave_a,
                param_b=opts.wave_b,
                stroke_style=stroke_style,
                hinge_group=hinge_group,
                rot_fn=rot_fn,
                offset_factor=column_offset_factor,
                point_in_polys=_point_in_polys,
            )
            return
        if pattern_type == "fabric":
            generate_fabric_pattern(
                polygons_rot=polygons_rot,
                min_x=min_x,
                max_x=max_x,
                min_y=min_y,
                max_y=max_y,
                cell_width=pattern_width,
                cell_height=slot_length,
                gap=slot_gap,
                spacing=column_spacing,
                stroke_style=stroke_style,
                hinge_group=hinge_group,
                rot_fn=rot_fn,
                offset_factor=column_offset_factor,
                point_in_polys=_point_in_polys,
            )
            return

        generate_line_pattern(
            intervals_fn=_intervals_at_x,
            min_x=min_x,
            max_x=max_x,
            min_y=min_y,
            max_y=max_y,
            column_spacing=column_spacing,
            slot_length=slot_length,
            slot_gap=slot_gap,
            stroke_style=stroke_style,
            hinge_group=hinge_group,
            rot_fn=rot_fn,
            offset_factor=column_offset_factor,
        )


if __name__ == "__main__":
    KMLivingHinge().run()
