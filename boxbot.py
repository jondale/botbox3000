#!/usr/bin/env python3

import sys
from pathlib import Path

deps_dir = Path(__file__).parent / "deps"
if deps_dir.exists() and str(deps_dir) not in sys.path:
    sys.path.insert(0, str(deps_dir))

import inkex
from inkex import PathElement, Group, TextElement
from offset import offset_path, boolean_lpe
from placements import pattern_along_path, calculate_path_length
from livinghinge import create_living_hinge_pattern, detect_straight_segments


class Boxbot(inkex.EffectExtension):
    CUT_OUTER_STYLE = {
        "stroke": "#cc0000",
        "stroke-width": "1mm",
        "-inkscape-stroke": "hairline",
        "fill": "none",
    }

    CUT_INNER_STYLE = {
        "stroke": "#ff66cc",
        "stroke-width": "1mm",
        "-inkscape-stroke": "hairline",
        "fill": "none",
    }

    META_STYLE = {
        "stroke": "#ffff00",
        "stroke-width": "1mm",
        "-inkscape-stroke": "hairline",
        "fill": "none",
    }

    LABEL_STYLE = {
        "font-size": "6px",
        "fill": "#ffff00",
        "font-family": "sans-serif",
        "text-anchor": "middle",
        "dominant-baseline": "middle",
    }

    def add_arguments(self, pars):
        pars.add_argument("--units", default="mm", help="Document units")
        pars.add_argument("--notebook", default="box", help="Active notebook tab")
        pars.add_argument("--generate_lid", type=inkex.Boolean, default=True, help="Generate lid")
        pars.add_argument("--material_thickness", type=float, default=3.0, help="Material thickness")
        pars.add_argument("--box_height", type=float, default=50.0, help="Box height")
        pars.add_argument("--tab_inset", type=float, default=5.0, help="Tab inset distance")
        pars.add_argument("--top_hole_inset", type=float, default=10.0, help="Top hole inset")
        pars.add_argument("--kerf", type=float, default=0.1, help="Kerf compensation")
        pars.add_argument("--tab_width", type=float, default=6.0, help="Tab width")
        pars.add_argument("--tab_start_offset", type=float, default=0.0, help="Tab start offset")
        pars.add_argument("--tab_border_radius", type=float, default=0.5, help="Tab border radius")
        pars.add_argument("--num_tabs", type=int, default=8, help="Number of tabs per side")
        pars.add_argument("--generate_living_hinge", type=inkex.Boolean, default=False, help="Generate living hinge pattern")
        pars.add_argument("--hinge_length_percent", type=int, default=25, help="Hinge cut length as percentage of side height")
        pars.add_argument("--hinge_gap", type=float, default=1.5, help="Hinge gap")
        pars.add_argument("--hinge_spacing", type=float, default=5.0, help="Hinge spacing")
        pars.add_argument("--magnet_type", default="none", help="Magnet type")
        pars.add_argument("--rectangle_magnet_width", type=float, default=6.0, help="Rectangle magnet width")
        pars.add_argument("--rectangle_magnet_height", type=float, default=2.0, help="Rectangle magnet height")
        pars.add_argument("--circle_magnet_diameter", type=float, default=6.0, help="Circle magnet diameter")
        pars.add_argument("--num_magnets", type=int, default=4, help="Number of magnets")
        pars.add_argument("--magnet_placement_offset", type=float, default=0.0, help="Magnet placement offset")
        pars.add_argument("--hide_magnets", type=inkex.Boolean, default=True, help="Hide magnets")

    def create_label(self, text, bbox, label_id):
        label = TextElement()
        label.set_id(self.svg.get_unique_id(label_id))
        label.set('x', str(bbox.center_x))
        label.set('y', str(bbox.center_y))
        label.style = self.LABEL_STYLE
        label.text = text
        return label

    def create_bottom_tabs_piece(self, inset_path_d):

        def create_tab(index):
            x = -tab_width / 2
            y = -tab_height / 2
            path_data = f"M {x},{y} L {x + tab_width},{y} L {x + tab_width},{y + tab_height} L {x},{y + tab_height} Z"

            tab = PathElement()
            tab.set_id(self.svg.get_unique_id(f"tab_{index}"))
            tab.set('d', path_data)
            return tab

        group = Group(id=self.svg.get_unique_id("boxbot"))
        self.svg.get_current_layer().add(group)

        self.inset_path = PathElement()
        self.inset_path.set_id(self.svg.get_unique_id("inset_path"))
        self.inset_path.set('d', inset_path_d)
        self.inset_path.style = self.META_STYLE
        group.append(self.inset_path)

        inset_csp = inkex.Path(inset_path_d).to_superpath()
        self.inset_length = sum(
            inkex.bezier.bezierlength((seg[1], seg[2], next_seg[0], next_seg[1]))
            for subpath in inset_csp
            for i, seg in enumerate(subpath[:-1])
            for next_seg in [subpath[i + 1]]
        )

        kerf = self.svg.unittouu(f"{self.options.kerf}{self.options.units}")
        tab_width = self.svg.unittouu(f"{self.options.tab_width}{self.options.units}") - kerf
        tab_height = self.svg.unittouu(f"{self.options.material_thickness}{self.options.units}") - kerf
        tab_start_offset = self.svg.unittouu(f"{self.options.tab_start_offset}{self.options.units}")

        self.tabs = pattern_along_path(
            inset_path_d,
            self.options.num_tabs,
            tab_width,
            tab_start_offset,
            "simple",
            create_tab
        )
        for tab in self.tabs:
            tab.style = self.CUT_INNER_STYLE
            group.append(tab)

        bottom_tabs_label = self.create_label("bottom tabs", group.bounding_box(), "bottom_tabs_label")
        group.append(bottom_tabs_label)
        self.bottom_inset = self.inset_path
        self.bottom_tab_holes = self.tabs

    def create_bottom_piece(self, offset_x):
        bottom_group = Group(id=self.svg.get_unique_id("bottom"))
        self.svg.get_current_layer().add(bottom_group)

        bottom_path = PathElement()
        bottom_path.set_id(self.svg.get_unique_id("bottom_path"))
        bottom_path.set('d', str(self.original_path))
        bottom_path.style = self.CUT_OUTER_STYLE
        bottom_group.append(bottom_path)

        bottom_inset = self.bottom_inset.copy()
        bottom_inset.set_id(self.svg.get_unique_id("bottom_inset"))
        bottom_group.append(bottom_inset)

        for i, tab in enumerate(self.bottom_tab_holes):
            bottom_tab = tab.copy()
            bottom_tab.set_id(self.svg.get_unique_id(f"bottom_tab_{i}"))
            bottom_tab.style = self.META_STYLE
            bottom_group.append(bottom_tab)

        bottom_bbox = bottom_group.bounding_box()
        bottom_label = self.create_label("bottom", bottom_bbox, "bottom_label")
        bottom_group.append(bottom_label)

        bottom_group.transform = inkex.Transform(translate=(offset_x, 0))

    def create_top_tabs_piece(self, offset_x):
        top_tabs_group = Group(id=self.svg.get_unique_id("top_tabs"))
        self.svg.get_current_layer().add(top_tabs_group)

        top_tabs_original = PathElement()
        top_tabs_original.set_id(self.svg.get_unique_id("top_tabs_original"))
        top_tabs_original.set('d', str(self.original_path))
        top_tabs_original.style = self.CUT_OUTER_STYLE
        top_tabs_group.append(top_tabs_original)

        top_tabs_inset = self.inset_path.copy()
        top_tabs_inset.set_id(self.svg.get_unique_id("top_tabs_inset"))
        top_tabs_group.append(top_tabs_inset)

        for tab in self.tabs:
            top_tab = tab.copy()
            top_tab.set_id(self.svg.get_unique_id("top_tab"))
            top_tabs_group.append(top_tab)

        from offset import offset_path as create_offset_path
        top_hole_inset_dist = -self.svg.unittouu(f"{self.options.top_hole_inset}{self.options.units}")
        self.top_hole_inset = None
        try:
            top_hole_inset_d = create_offset_path(self.original_path, top_hole_inset_dist)
            self.top_hole_inset = PathElement()
            self.top_hole_inset.set_id(self.svg.get_unique_id("top_hole_inset"))
            self.top_hole_inset.set('d', top_hole_inset_d)
            self.top_hole_inset.style = self.CUT_INNER_STYLE
            top_tabs_group.append(self.top_hole_inset)
        except ValueError:
            pass

        self.magnets = []
        if self.options.magnet_type != "none":
            num_magnets = self.options.num_magnets
            magnet_placement_offset = self.svg.unittouu(f"{self.options.magnet_placement_offset}{self.options.units}")
            inset_path_d = self.inset_path.get('d')

            def create_magnet(index):
                if self.options.magnet_type == "rectangle":
                    magnet_width = self.svg.unittouu(f"{self.options.rectangle_magnet_width}{self.options.units}")
                    magnet_height = self.svg.unittouu(f"{self.options.rectangle_magnet_height}{self.options.units}")

                    rect_x = -magnet_width / 2
                    rect_y = -magnet_height / 2
                    path_data = (
                        f"M {rect_x},{rect_y} "
                        f"L {rect_x + magnet_width},{rect_y} "
                        f"L {rect_x + magnet_width},{rect_y + magnet_height} "
                        f"L {rect_x},{rect_y + magnet_height} Z"
                    )
                else:
                    magnet_diameter = self.svg.unittouu(f"{self.options.circle_magnet_diameter}{self.options.units}")
                    radius = magnet_diameter / 2
                    path_data = (
                        f"M {radius},0 "
                        f"A {radius},{radius} 0 0 1 0,{radius} "
                        f"A {radius},{radius} 0 0 1 {-radius},0 "
                        f"A {radius},{radius} 0 0 1 0,{-radius} "
                        f"A {radius},{radius} 0 0 1 {radius},0 Z"
                    )

                magnet = PathElement()
                magnet.set_id(self.svg.get_unique_id(f"magnet_{index}"))
                magnet.set('d', path_data)
                magnet.style = self.CUT_OUTER_STYLE if self.options.hide_magnets else self.META_STYLE
                return magnet

            if self.options.magnet_type == "rectangle":
                item_width = self.svg.unittouu(f"{self.options.rectangle_magnet_width}{self.options.units}")
            else:
                item_width = self.svg.unittouu(f"{self.options.circle_magnet_diameter}{self.options.units}")

            self.magnets = pattern_along_path(
                inset_path_d,
                num_magnets,
                item_width,
                magnet_placement_offset,
                "even",
                create_magnet
            )

            for magnet in self.magnets:
                top_tabs_group.append(magnet)

        top_tabs_bbox = top_tabs_group.bounding_box()
        top_tabs_label = self.create_label("top tabs", top_tabs_bbox, "top_tabs_label")
        top_tabs_group.append(top_tabs_label)
        top_tabs_group.transform = inkex.Transform(translate=(offset_x, 0))

    def create_top_piece(self, offset_x):
        top_group = Group(id=self.svg.get_unique_id("top"))
        self.svg.get_current_layer().add(top_group)

        top_path = PathElement()
        top_path.set_id(self.svg.get_unique_id("top_path"))
        top_path.set('d', str(self.original_path))
        top_path.style = self.CUT_OUTER_STYLE
        top_group.append(top_path)

        top_inset = self.inset_path.copy()
        top_inset.set_id(self.svg.get_unique_id("top_inset"))
        top_group.append(top_inset)

        for tab in self.tabs:
            top_tab = tab.copy()
            top_tab.set_id(self.svg.get_unique_id("top_tab"))
            top_tab.style = self.META_STYLE
            top_group.append(top_tab)

        if self.top_hole_inset is not None:
            top_hole_inset_copy = self.top_hole_inset.copy()
            top_hole_inset_copy.set_id(self.svg.get_unique_id("top_hole_inset"))
            top_group.append(top_hole_inset_copy)

        if len(self.magnets) > 0:
            for i, magnet in enumerate(self.magnets):
                magnet_copy = magnet.copy()
                magnet_copy.set_id(self.svg.get_unique_id(f"top_magnet_{i}"))
                magnet_copy.style = self.META_STYLE if self.options.hide_magnets else self.CUT_OUTER_STYLE
                top_group.append(magnet_copy)

        top_bbox = top_group.bounding_box()
        top_label = self.create_label("top", top_bbox, "top_label")
        top_group.append(top_label)
        top_group.transform = inkex.Transform(translate=(offset_x, 0))

    def create_side_piece(self, offset_x, offset_y, inset_path_d):

        side_group = Group(id=self.svg.get_unique_id("side"))
        self.svg.get_current_layer().add(side_group)

        tab_width = self.svg.unittouu(f"{self.options.tab_width}{self.options.units}")
        tab_height = self.svg.unittouu(f"{self.options.material_thickness}{self.options.units}")
        tab_start_offset = self.svg.unittouu(f"{self.options.tab_start_offset}{self.options.units}")
        num_tabs = self.options.num_tabs

        rect_width = self.inset_length
        rect_height = (self.svg.unittouu(f"{self.options.box_height}{self.options.units}") -
                      4 * self.svg.unittouu(f"{self.options.material_thickness}{self.options.units}"))

        rect_path_data = f"M 0,0 L {rect_width},0 L {rect_width},{rect_height} L 0,{rect_height} Z"

        side_rect = PathElement()
        side_rect.set_id(self.svg.get_unique_id("side_rect"))
        side_rect.set('d', rect_path_data)
        side_rect.style = self.CUT_OUTER_STYLE
        side_rect.transform = inkex.Transform(translate=(offset_x, offset_y))
        side_group.append(side_rect)

        corner_radius = self.svg.unittouu(f"{self.options.tab_border_radius}{self.options.units}")
        total_tabs = num_tabs + 1
        half_tab_width = tab_width / 2

        full_tab_height = rect_height + 2 * tab_height
        tab_y = -tab_height

        tab_elements = []

        for i in range(total_tabs):
            if i == 0:
                current_tab_width = half_tab_width
                tab_x = 0
            elif i == total_tabs - 1:
                current_tab_width = half_tab_width
                tab_x = rect_width - half_tab_width
            else:
                current_tab_width = tab_width
                spacing = rect_width / num_tabs
                tab_x = i * spacing - current_tab_width / 2

            r = min(corner_radius, current_tab_width / 2, full_tab_height / 2)
            tab_path = (
                f"M {tab_x + r},{tab_y} "
                f"L {tab_x + current_tab_width - r},{tab_y} "
                f"A {r},{r} 0 0 1 {tab_x + current_tab_width},{tab_y + r} "
                f"L {tab_x + current_tab_width},{tab_y + full_tab_height - r} "
                f"A {r},{r} 0 0 1 {tab_x + current_tab_width - r},{tab_y + full_tab_height} "
                f"L {tab_x + r},{tab_y + full_tab_height} "
                f"A {r},{r} 0 0 1 {tab_x},{tab_y + full_tab_height - r} "
                f"L {tab_x},{tab_y + r} "
                f"A {r},{r} 0 0 1 {tab_x + r},{tab_y} "
                f"Z"
            )

            tab_elem = PathElement()
            tab_elem.set_id(self.svg.get_unique_id("side_tab"))
            tab_elem.set('d', tab_path)
            tab_elem.style = self.META_STYLE
            tab_elem.transform = inkex.Transform(translate=(offset_x, offset_y))
            side_group.append(tab_elem)
            tab_elements.append(tab_elem)

        boolean_lpe(self.svg, side_rect, tab_elements, operation="union")

        path = inkex.Path(inset_path_d)
        total_length = calculate_path_length(path)

        gap = (total_length - num_tabs * tab_width) / num_tabs
        first_tab_start = tab_start_offset % total_length
        first_tab_center = (first_tab_start + tab_width / 2) % total_length
        side_start_offset = first_tab_center

        straight_segments = detect_straight_segments(inset_path_d, 20.0, self.svg, self.options.units)

        adjusted_straight_segments = []
        for seg_start, seg_end in straight_segments:
            start_pos = (seg_start - side_start_offset) % total_length
            end_pos = (seg_end - side_start_offset) % total_length

            if start_pos < end_pos:
                adjusted_straight_segments.append((start_pos, end_pos))
            else:
                adjusted_straight_segments.append((start_pos, total_length))
                adjusted_straight_segments.append((0, end_pos))

        hinge_regions = []
        if not adjusted_straight_segments:
            hinge_regions = [(0, rect_width)]
        else:
            adjusted_straight_segments = sorted(adjusted_straight_segments, key=lambda x: x[0])

            current_pos = 0
            for seg_start, seg_end in adjusted_straight_segments:
                if current_pos < seg_start:
                    hinge_regions.append((current_pos, seg_start))
                current_pos = seg_end

            if current_pos < rect_width:
                hinge_regions.append((current_pos, rect_width))

        for i, (hinge_start, hinge_end) in enumerate(hinge_regions):
            hinge_rect_data = f"M {hinge_start},0 L {hinge_end},0 L {hinge_end},{rect_height} L {hinge_start},{rect_height} Z"

            hinge_rect = PathElement()
            hinge_rect.set_id(self.svg.get_unique_id(f"hinge_rect_{i}"))
            hinge_rect.set('d', hinge_rect_data)
            hinge_rect.style = self.META_STYLE
            hinge_rect.transform = inkex.Transform(translate=(offset_x, offset_y))
            side_group.append(hinge_rect)

            if self.options.generate_living_hinge:
                hinge_width = hinge_end - hinge_start
                hinge_length_param = rect_height * (self.options.hinge_length_percent / 100.0)
                hinge_gap = self.svg.unittouu(f"{self.options.hinge_gap}{self.options.units}")
                hinge_spacing = self.svg.unittouu(f"{self.options.hinge_spacing}{self.options.units}")

                hinge_cuts = create_living_hinge_pattern(
                    self.svg,
                    hinge_length_param,
                    hinge_gap,
                    hinge_spacing,
                    hinge_width,
                    rect_height,
                    offset_x + hinge_start,
                    offset_y,
                    self.CUT_INNER_STYLE,
                    tab_positions=None,
                    segment_start=0
                )

                for hinge_cut in hinge_cuts:
                    side_group.append(hinge_cut)

        side_bbox = side_group.bounding_box()
        side_label = self.create_label("side", side_bbox, "side_label")
        side_group.append(side_label)

        self.side_group = side_group

    def create_lid_top_piece(self, offset_x, offset_y):
        lid_top_group = Group(id=self.svg.get_unique_id("lid_top"))
        self.svg.get_current_layer().add(lid_top_group)

        lid_top_path = PathElement()
        lid_top_path.set_id(self.svg.get_unique_id("lid_top_path"))
        lid_top_path.set('d', str(self.original_path))
        lid_top_path.style = self.CUT_OUTER_STYLE
        lid_top_group.append(lid_top_path)

        lid_top_inset = self.inset_path.copy()
        lid_top_inset.set_id(self.svg.get_unique_id("lid_top_inset"))
        lid_top_group.append(lid_top_inset)

        for i, magnet in enumerate(self.magnets):
            lid_top_magnet = magnet.copy()
            lid_top_magnet.set_id(self.svg.get_unique_id(f"lid_top_magnet_{i}"))
            lid_top_magnet.style = self.META_STYLE
            lid_top_group.append(lid_top_magnet)

        lid_top_bbox_local = lid_top_group.bounding_box()
        lid_top_label = self.create_label("lid top", lid_top_bbox_local, "lid_top_label")
        lid_top_group.append(lid_top_label)

        lid_top_group.transform = inkex.Transform(translate=(offset_x, offset_y))

        return lid_top_group.bounding_box()

    def create_lid_middle_piece(self, offset_x, offset_y):
        lid_middle_group = Group(id=self.svg.get_unique_id("lid_middle"))
        self.svg.get_current_layer().add(lid_middle_group)

        lid_middle_path = PathElement()
        lid_middle_path.set_id(self.svg.get_unique_id("lid_middle_path"))
        lid_middle_path.set('d', str(self.original_path))
        lid_middle_path.style = self.CUT_OUTER_STYLE
        lid_middle_group.append(lid_middle_path)

        lid_middle_inset = self.inset_path.copy()
        lid_middle_inset.set_id(self.svg.get_unique_id("lid_middle_inset"))
        lid_middle_group.append(lid_middle_inset)

        for i, magnet in enumerate(self.magnets):
            lid_middle_magnet = magnet.copy()
            lid_middle_magnet.set_id(self.svg.get_unique_id(f"lid_middle_magnet_{i}"))
            lid_middle_magnet.style = self.CUT_OUTER_STYLE if self.options.hide_magnets else self.META_STYLE
            lid_middle_group.append(lid_middle_magnet)

        lid_middle_bbox_local = lid_middle_group.bounding_box()
        lid_middle_label = self.create_label("lid middle", lid_middle_bbox_local, "lid_middle_label")
        lid_middle_group.append(lid_middle_label)

        lid_middle_group.transform = inkex.Transform(translate=(offset_x, offset_y))

        return lid_middle_group.bounding_box()

    def create_lid_bottom_piece(self, offset_x, offset_y):
        lid_bottom_group = Group(id=self.svg.get_unique_id("lid_bottom"))
        self.svg.get_current_layer().add(lid_bottom_group)

        lid_bottom_path = PathElement()
        lid_bottom_path.set_id(self.svg.get_unique_id("lid_bottom_path"))
        lid_bottom_path.set('d', str(self.original_path))
        lid_bottom_path.style = self.CUT_OUTER_STYLE
        lid_bottom_group.append(lid_bottom_path)

        lid_bottom_inset = self.inset_path.copy()
        lid_bottom_inset.set_id(self.svg.get_unique_id("lid_bottom_inset"))
        lid_bottom_group.append(lid_bottom_inset)

        for i, magnet in enumerate(self.magnets):
            lid_bottom_magnet = magnet.copy()
            lid_bottom_magnet.set_id(self.svg.get_unique_id(f"lid_bottom_magnet_{i}"))
            lid_bottom_magnet.style = self.CUT_OUTER_STYLE if not self.options.hide_magnets else self.META_STYLE
            lid_bottom_group.append(lid_bottom_magnet)

        lid_bottom_bbox_local = lid_bottom_group.bounding_box()
        lid_bottom_label = self.create_label("lid bottom", lid_bottom_bbox_local, "lid_bottom_label")
        lid_bottom_group.append(lid_bottom_label)

        lid_bottom_group.transform = inkex.Transform(translate=(offset_x, offset_y))

        return lid_bottom_group.bounding_box()

    def create_lid_fitting_piece(self, offset_x, offset_y):
        lid_fitting_group = Group(id=self.svg.get_unique_id("lid_fitting"))
        self.svg.get_current_layer().add(lid_fitting_group)

        top_hole_inset = self.svg.unittouu(f"{self.options.top_hole_inset}{self.options.units}")
        extra_inset = self.svg.unittouu("1mm")
        lid_offset_dist = -(top_hole_inset + extra_inset)

        try:
            from offset import offset_path
            lid_fitting_path_d = offset_path(self.original_path, lid_offset_dist)
            lid_fitting_path = PathElement()
            lid_fitting_path.set_id(self.svg.get_unique_id("lid_fitting_path"))
            lid_fitting_path.set('d', lid_fitting_path_d)
            lid_fitting_path.style = self.CUT_OUTER_STYLE
            lid_fitting_group.append(lid_fitting_path)

            lid_fitting_bbox_local = lid_fitting_group.bounding_box()
            lid_fitting_label = self.create_label("lid fitting", lid_fitting_bbox_local, "lid_fitting_label")
            lid_fitting_group.append(lid_fitting_label)

            lid_fitting_group.transform = inkex.Transform(translate=(offset_x, offset_y))

            return lid_fitting_group.bounding_box()
        except ValueError:
            return None

    def effect(self):
        if not self.svg.selection:
            raise inkex.AbortExtension("Select a single path.")

        selected_element = list(self.svg.selection.values())[0]
        node = selected_element

        if not isinstance(node, PathElement):
            if hasattr(node, 'path') and node.path is not None:
                path_element = PathElement()
                path_element.path = node.path
                path_element.style = node.style
                path_element.transform = node.transform
                node = path_element
            else:
                try:
                    node = node.to_path_element()
                except Exception:
                    raise inkex.AbortExtension("Selection must be a path or convertible to a path.")

        current_layer = self.svg.get_current_layer()
        layer_transform = current_layer.composed_transform()
        layer_transform_inv = -layer_transform

        doc_path = node.path.to_absolute().transform(selected_element.composed_transform())
        self.original_path = doc_path.transform(layer_transform_inv)
        self.original_path_bbox = self.original_path.bounding_box()

        selected_element.style = self.CUT_OUTER_STYLE

        tab_height = self.svg.unittouu(f"{self.options.material_thickness}{self.options.units}")

        try:
            offset_dist = -self.svg.unittouu(f"{self.options.tab_inset}{self.options.units}")
            inset_path_d = offset_path(self.original_path, offset_dist)
        except ValueError as e:
            raise inkex.AbortExtension(str(e))

        self.create_bottom_tabs_piece(inset_path_d)
        offset_x = self.original_path_bbox.width + self.svg.unittouu("2mm")
        self.create_bottom_piece(offset_x)
        self.create_top_tabs_piece(2 * offset_x)
        self.create_top_piece(3 * offset_x)

        offset_x = self.original_path_bbox.left
        offset_y = self.original_path_bbox.bottom + self.svg.unittouu("2mm") + tab_height
        self.create_side_piece(offset_x, offset_y, inset_path_d)

        if self.options.generate_lid:
            side_bbox_with_tabs = self.side_group.bounding_box()
            lid_target_x = self.original_path_bbox.left
            lid_target_y = side_bbox_with_tabs.bottom + self.svg.unittouu("2mm")

            translate_x = lid_target_x - self.original_path_bbox.left
            translate_y = lid_target_y - self.original_path_bbox.top

            lid_top_bbox = self.create_lid_top_piece(translate_x, translate_y)

            lid_middle_offset_x = lid_top_bbox.right + self.svg.unittouu("2mm") - self.original_path_bbox.left
            lid_middle_bbox = self.create_lid_middle_piece(lid_middle_offset_x, translate_y)

            lid_bottom_offset_x = lid_middle_bbox.right + self.svg.unittouu("2mm") - self.original_path_bbox.left
            lid_bottom_bbox = self.create_lid_bottom_piece(lid_bottom_offset_x, translate_y)

            lid_fitting_offset_x = lid_bottom_bbox.right + self.svg.unittouu("2mm") - self.original_path_bbox.left
            self.create_lid_fitting_piece(lid_fitting_offset_x, translate_y)


if __name__ == "__main__":
    Boxbot().run()
