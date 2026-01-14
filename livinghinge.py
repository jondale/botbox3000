#!/usr/bin/env python3

import sys
from pathlib import Path

deps_dir = Path(__file__).parent / "deps"
if deps_dir.exists() and str(deps_dir) not in sys.path:
    sys.path.insert(0, str(deps_dir))

import inkex
from inkex import PathElement, Transform


def create_living_hinge_pattern(svg, hinge_length, hinge_gap, hinge_spacing, width, height,
                                offset_x, offset_y, cut_style, tab_positions=None, segment_start=0):
    hinges = []
    x_pos = hinge_spacing / 2
    col = 0

    while x_pos < width:
        y_start = hinge_gap if col % 2 == 0 else hinge_gap + hinge_length / 2

        if col % 2 == 0:
            top_cut_end = hinge_gap
            top_cut_start = max(0, top_cut_end - hinge_length)
        else:
            top_cut_end = hinge_gap + hinge_length / 2 - hinge_spacing
            top_cut_start = max(0, top_cut_end - hinge_length)

        if top_cut_start < top_cut_end and top_cut_end > 0:
            hinge_path_data = f"M {x_pos},{top_cut_start} L {x_pos},{top_cut_end}"
            hinge = PathElement()
            hinge.set_id(svg.get_unique_id(f"hinge_{col}_top"))
            hinge.set('d', hinge_path_data)
            hinge.style = cut_style
            hinge.transform = inkex.Transform(translate=(offset_x, offset_y))
            hinges.append(hinge)

        y_pos = y_start
        cut_index = 0
        while y_pos + hinge_length <= height - hinge_gap:
            hinge_abs_start = segment_start + x_pos
            hinge_abs_end = segment_start + x_pos

            hinge_path_data = f"M {x_pos},{y_pos} L {x_pos},{y_pos + hinge_length}"

            hinge = PathElement()
            hinge.set_id(svg.get_unique_id(f"hinge_{col}_{cut_index}"))
            hinge.set('d', hinge_path_data)
            hinge.style = cut_style
            hinge.transform = inkex.Transform(translate=(offset_x, offset_y))
            hinges.append(hinge)

            y_pos += hinge_length + hinge_spacing
            cut_index += 1

        bottom_cut_start = y_pos
        bottom_cut_end = min(height, bottom_cut_start + hinge_length)

        if bottom_cut_start < height and bottom_cut_end > bottom_cut_start:
            hinge_path_data = f"M {x_pos},{bottom_cut_start} L {x_pos},{bottom_cut_end}"
            hinge = PathElement()
            hinge.set_id(svg.get_unique_id(f"hinge_{col}_bottom"))
            hinge.set('d', hinge_path_data)
            hinge.style = cut_style
            hinge.transform = inkex.Transform(translate=(offset_x, offset_y))
            hinges.append(hinge)

        x_pos += hinge_spacing
        col += 1

    return hinges


def detect_straight_segments(inset_path_d, min_straight_length, svg, units):
    path = inkex.Path(inset_path_d)
    csp = path.to_superpath()

    min_length_uu = svg.unittouu(f"{min_straight_length}{units}")

    straight_segments = []
    current_distance = 0.0

    for subpath in csp:
        for i, seg in enumerate(subpath[:-1]):
            next_seg = subpath[i + 1]
            bezier = (seg[1], seg[2], next_seg[0], next_seg[1])
            seg_length = inkex.bezier.bezierlength(bezier)

            if seg_length >= min_length_uu:
                straight_segments.append((current_distance, current_distance + seg_length))

            current_distance += seg_length

    return straight_segments
