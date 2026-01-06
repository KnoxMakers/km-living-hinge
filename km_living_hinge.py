#!/usr/bin/env python3

#################################################
#
#  KM Living Hinge 
#  A highly opinionated living hinge generator
#
#  With love, by Jondale
#
#################################################

import math
import inkex
from inkex import ShapeElement, bezier

from shapes import get_shape, get_config
from livinghinge import generate_hinge, segments_to_svg_paths


class KMLivingHinge(inkex.EffectExtension):
    def add_arguments(self, pars) -> None:
        pars.add_argument("--units", default="mm")
        pars.add_argument("--angle", type=float, default=0.0)
        pars.add_argument("--type", default="line")
        pars.add_argument("--line_height_pct", type=int, default=80)
        pars.add_argument("--line_x_spacing", type=float, default=2.0)
        pars.add_argument("--line_y_spacing", type=float, default=2.0)
        pars.add_argument("--fishbone_height", type=float, default=10.0)
        pars.add_argument("--fishbone_width", type=float, default=5.0)
        pars.add_argument("--fishbone_x_spacing", type=float, default=2.0)
        pars.add_argument("--fishbone_y_spacing", type=float, default=2.0)
        pars.add_argument("--cross_height", type=float, default=10.0)
        pars.add_argument("--cross_width", type=float, default=5.0)
        pars.add_argument("--bezier_height", type=float, default=10.0)
        pars.add_argument("--bezier_width", type=float, default=5.0)
        pars.add_argument("--bezier_x_spacing", type=float, default=2.0)
        pars.add_argument("--bezier_y_spacing", type=float, default=2.0)
        pars.add_argument("--wave_height", type=float, default=10.0)
        pars.add_argument("--wave_width", type=float, default=5.0)
        pars.add_argument("--fabric_height", type=float, default=10.0)
        pars.add_argument("--fabric_width", type=float, default=5.0)

    def effect(self) -> None:
        opts = self.options
        pattern_type = opts.type or "line"
        if pattern_type not in ("line", "fishbone", "cross", "bezier", "wave", "fabric"):
            pattern_type = "line"

        selection = getattr(self.svg, "selection", None)
        if not selection or len(selection) == 0:
            raise inkex.AbortExtension(
                "Select a shape (path, rectangle, circle, etc.); the hinge fills and is trimmed to your selection."
            )
        selected_elems = list(selection)

        def _uu(value, unit):
            return float(self.svg.unittouu(f"{value}{unit}"))

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
                    if poly[0] != poly[-1]:
                        poly.append(poly[0])
                    polys.append(poly)
            return polys

        seen_shapes = set()
        shapes_to_process = []

        def _iter_shapes(elem):
            if isinstance(elem, ShapeElement) and not isinstance(elem, inkex.Group):
                yield elem
            if isinstance(elem, inkex.Group):
                for child in elem.iterdescendants():
                    if isinstance(child, ShapeElement) and not isinstance(child, inkex.Group):
                        yield child
                return
            for child in elem.iterdescendants():
                if isinstance(child, ShapeElement) and not isinstance(child, inkex.Group):
                    yield child

        for elem in selected_elems:
            for shape in _iter_shapes(elem):
                key = getattr(shape, "get_id", lambda: None)() or shape.get("id") or id(shape)
                if key in seen_shapes:
                    continue
                seen_shapes.add(key)
                shapes_to_process.append(shape)

        if not shapes_to_process:
            raise inkex.AbortExtension("Unable to read the selected shape geometry.")

        min_x, min_y, max_x, max_y = float('inf'), float('inf'), float('-inf'), float('-inf')
        for shape in shapes_to_process:
            bbox = shape.bounding_box(shape.composed_transform())
            if bbox:
                min_x = min(min_x, bbox.left)
                min_y = min(min_y, bbox.top)
                max_x = max(max_x, bbox.right)
                max_y = max(max_y, bbox.bottom)
        bbox_width = max_x - min_x
        bbox_height = max_y - min_y
        bbox = (min_x, min_y, bbox_width, bbox_height)

        unit = opts.units
        angle_rad = math.radians(float(opts.angle))

        if pattern_type == "line":
            height = opts.line_height_pct / 100.0
            width = 0
            x_spacing = _uu(opts.line_x_spacing, unit)
            y_spacing = _uu(opts.line_y_spacing, unit)
        elif pattern_type == "fishbone":
            height = _uu(opts.fishbone_height, unit)
            width = _uu(opts.fishbone_width, unit)
            x_spacing = _uu(opts.fishbone_x_spacing, unit)
            y_spacing = _uu(opts.fishbone_y_spacing, unit)
        elif pattern_type == "cross":
            height = _uu(opts.cross_height, unit)
            width = _uu(opts.cross_width, unit)
            x_spacing = 0
            y_spacing = 0
        elif pattern_type == "bezier":
            height = _uu(opts.bezier_height, unit)
            width = _uu(opts.bezier_width, unit)
            x_spacing = _uu(opts.bezier_x_spacing, unit)
            y_spacing = _uu(opts.bezier_y_spacing, unit)
        elif pattern_type == "wave":
            height = _uu(opts.wave_height, unit)
            width = _uu(opts.wave_width, unit)
            x_spacing = 0
            y_spacing = 0
        elif pattern_type == "fabric":
            height = _uu(opts.fabric_height, unit)
            width = _uu(opts.fabric_width, unit)
            x_spacing = 0
            y_spacing = 0
        else:
            height = opts.line_height_pct / 100.0
            width = 0
            x_spacing = _uu(opts.line_x_spacing, unit)
            y_spacing = _uu(opts.line_y_spacing, unit)

        config_fn = get_config(pattern_type)
        height, width, x_spacing, y_spacing, y_offset = config_fn(
            height, width, x_spacing, y_spacing, bbox
        )

        if height <= 0:
            raise inkex.AbortExtension("Height must be greater than zero.")
        if width < 0:
            raise inkex.AbortExtension("Width must not be negative.")

        stroke_width = float(self.svg.unittouu("0.25mm"))
        stroke_style = {
            "stroke": "#000000",
            "stroke-width": str(stroke_width),
            "fill": "none",
            "stroke-linecap": "round",
        }

        parent = self.svg.get_current_layer()
        hinge_group = inkex.Group(id=self.svg.get_unique_id("km-living-hinge"))
        hinge_group.set("{http://www.inkscape.org/namespaces/inkscape}label", "KM Living Hinge")
        parent.add(hinge_group)

        shape_fn = get_shape(pattern_type)

        for shape in shapes_to_process:
            shape_path = shape.to_path_element().path.transform(shape.composed_transform())
            csp = shape_path.to_superpath()
            bezier.cspsubdiv(csp, 0.25)
            polygons = _superpath_to_polygons(csp)
            if not polygons:
                continue

            segments = generate_hinge(
                polygons=polygons,
                shape_fn=shape_fn,
                height=height,
                width=width,
                x_spacing=x_spacing,
                y_spacing=y_spacing,
                y_offset=y_offset,
                angle_rad=angle_rad,
            )

            segments_to_svg_paths(segments, stroke_style, hinge_group)


if __name__ == "__main__":
    KMLivingHinge().run()
