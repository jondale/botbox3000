#!/usr/bin/env python3

import sys
from pathlib import Path

deps_dir = Path(__file__).parent / "deps"
if deps_dir.exists() and str(deps_dir) not in sys.path:
    sys.path.insert(0, str(deps_dir))

import math
import inkex
from inkex import PathElement, Rectangle, Transform


def calculate_path_length(path):
    if isinstance(path, str):
        path = inkex.Path(path)

    csp = path.to_superpath()
    total_length = 0.0

    for subpath in csp:
        for i, seg in enumerate(subpath[:-1]):
            next_seg = subpath[i + 1]
            bezier = (seg[1], seg[2], next_seg[0], next_seg[1])
            seg_length = inkex.bezier.bezierlength(bezier, tolerance=0.01)
            total_length += seg_length

    return total_length


def point_at_length(path, target_length):
    if isinstance(path, str):
        path = inkex.Path(path)

    csp = path.to_superpath()
    current_length = 0.0

    for subpath in csp:
        for i, seg in enumerate(subpath[:-1]):
            next_seg = subpath[i + 1]
            bezier = (seg[1], seg[2], next_seg[0], next_seg[1])
            seg_length = inkex.bezier.bezierlength(bezier, tolerance=0.01)

            if current_length + seg_length >= target_length:
                t = (target_length - current_length) / seg_length if seg_length > 0 else 0
                t = max(0.0, min(1.0, t))

                p0, p1, p2, p3 = bezier
                p0_p1_dist = ((p1[0] - p0[0])**2 + (p1[1] - p0[1])**2)**0.5
                p2_p3_dist = ((p3[0] - p2[0])**2 + (p3[1] - p2[1])**2)**0.5

                if p0_p1_dist < 0.001 and p2_p3_dist < 0.001:
                    point = (
                        p0[0] + t * (p3[0] - p0[0]),
                        p0[1] + t * (p3[1] - p0[1])
                    )
                else:
                    point = inkex.bezier.bezierpointatt(bezier, t)

                p0, p1, p2, p3 = bezier
                one_minus_t = 1.0 - t

                dx = (3 * one_minus_t * one_minus_t * (p1[0] - p0[0]) +
                      6 * one_minus_t * t * (p2[0] - p1[0]) +
                      3 * t * t * (p3[0] - p2[0]))
                dy = (3 * one_minus_t * one_minus_t * (p1[1] - p0[1]) +
                      6 * one_minus_t * t * (p2[1] - p1[1]) +
                      3 * t * t * (p3[1] - p2[1]))

                length = (dx * dx + dy * dy) ** 0.5
                if length > 0:
                    dx /= length
                    dy /= length

                return (point[0], point[1]), (dx, dy)

            current_length += seg_length

    last_subpath = csp[-1]
    last_point = last_subpath[-1][1]
    return (last_point[0], last_point[1]), (1.0, 0.0)


def pattern_along_path(path, num_items, item_width, start_offset, spacing, create_shape_fn):

    if isinstance(path, str):
        path = inkex.Path(path)

    if num_items <= 0:
        return []

    total_length = calculate_path_length(path)
    items = []

    if spacing == "even":
        gap = (total_length - num_items * item_width) / num_items

        for i in range(num_items):
            item_start = (start_offset + i * (gap + item_width)) % total_length
            item_center = (item_start + item_width / 2) % total_length

            point, tangent = point_at_length(path, item_center)
            angle = math.degrees(math.atan2(tangent[1], tangent[0]))

            item = create_shape_fn(i)

            transform = Transform()
            transform.add_translate(point[0], point[1])
            transform.add_rotate(angle)

            item.transform = transform
            items.append(item)

    elif spacing == "endpoints":
        for i in range(num_items):
            base_distance = total_length * i / (num_items - 1) if num_items > 1 else 0
            distance = (base_distance + start_offset) % total_length
            point, tangent = point_at_length(path, distance)
            angle = math.degrees(math.atan2(tangent[1], tangent[0]))

            item = create_shape_fn(i)

            transform = Transform()
            transform.add_translate(point[0], point[1])
            transform.add_rotate(angle)

            item.transform = transform
            items.append(item)

    elif spacing == "simple":
        gap = (total_length - num_items * item_width) / num_items

        for i in range(num_items):
            item_start = (start_offset + i * (gap + item_width)) % total_length
            distance = (item_start + item_width / 2) % total_length
            point, tangent = point_at_length(path, distance)
            angle = math.degrees(math.atan2(tangent[1], tangent[0]))

            item = create_shape_fn(i)

            transform = Transform()
            transform.add_translate(point[0], point[1])
            transform.add_rotate(angle)

            item.transform = transform
            items.append(item)

    return items
