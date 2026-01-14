#!/usr/bin/env python3

import math

try:
    from inkex import Path
except ImportError:
    Path = None


def subpath_to_points(subpath, precision=1.0):
    points = []
    current_point = (0, 0)

    for cmd in subpath:
        if isinstance(cmd, tuple):
            letter = cmd[0].upper()
            coord = cmd[1]
        else:
            letter = cmd.letter.upper()
            args = cmd.args

        if letter == 'M':
            if isinstance(cmd, tuple):
                current_point = coord
            else:
                current_point = (args[0], args[1])
            points.append(current_point)

        elif letter == 'L':
            if isinstance(cmd, tuple):
                current_point = coord
            else:
                current_point = (args[0], args[1])
            points.append(current_point)

        elif letter == 'H':
            if isinstance(cmd, tuple):
                current_point = (coord[0], current_point[1])
            else:
                current_point = (args[0], current_point[1])
            points.append(current_point)

        elif letter == 'V':
            if isinstance(cmd, tuple):
                current_point = (current_point[0], coord[1])
            else:
                current_point = (current_point[0], args[0])
            points.append(current_point)

        elif letter == 'C':
            p0 = current_point
            p1 = (args[0], args[1])
            p2 = (args[2], args[3])
            p3 = (args[4], args[5])

            chord_length = distance(p0, p3)
            control_length = distance(p0, p1) + distance(p1, p2) + distance(p2, p3)
            approx_length = (chord_length + control_length) / 2

            num_segments = max(2, int(approx_length / precision))

            for i in range(1, num_segments + 1):
                t = i / num_segments
                point = cubic_bezier_point(p0, p1, p2, p3, t)
                points.append(point)

            current_point = p3

        elif letter == 'S':
            p0 = current_point
            p3 = (args[2], args[3])

            chord_length = distance(p0, p3)
            num_segments = max(2, int(chord_length / precision))

            for i in range(1, num_segments + 1):
                t = i / num_segments
                x = p0[0] + t * (p3[0] - p0[0])
                y = p0[1] + t * (p3[1] - p0[1])
                points.append((x, y))

            current_point = p3

        elif letter == 'Q':
            p0 = current_point
            p1 = (args[0], args[1])
            p2 = (args[2], args[3])

            chord_length = distance(p0, p2)
            control_length = distance(p0, p1) + distance(p1, p2)
            approx_length = (chord_length + control_length) / 2

            num_segments = max(2, int(approx_length / precision))

            for i in range(1, num_segments + 1):
                t = i / num_segments
                point = quadratic_bezier_point(p0, p1, p2, t)
                points.append(point)

            current_point = p2

        elif letter == 'T':
            p0 = current_point
            p2 = (args[0], args[1])

            chord_length = distance(p0, p2)
            num_segments = max(2, int(chord_length / precision))

            for i in range(1, num_segments + 1):
                t = i / num_segments
                x = p0[0] + t * (p2[0] - p0[0])
                y = p0[1] + t * (p2[1] - p0[1])
                points.append((x, y))

            current_point = p2

        elif letter == 'A':
            rx = abs(args[0])
            ry = abs(args[1])
            x_axis_rotation = args[2]
            large_arc_flag = args[3]
            sweep_flag = args[4]
            end_x = args[5]
            end_y = args[6]

            start_x, start_y = current_point

            beziers = arc_to_beziers(start_x, start_y, rx, ry, x_axis_rotation,
                                     large_arc_flag, sweep_flag, end_x, end_y)

            for bez in beziers:
                p0, p1, p2, p3 = bez
                chord_length = distance(p0, p3)
                control_length = distance(p0, p1) + distance(p1, p2) + distance(p2, p3)
                approx_length = (chord_length + control_length) / 2

                num_segments = max(2, int(approx_length / precision))

                for i in range(1, num_segments + 1):
                    t = i / num_segments
                    point = cubic_bezier_point(p0, p1, p2, p3, t)
                    points.append(point)

            current_point = (end_x, end_y)

    return points


def arc_to_beziers(x1, y1, rx, ry, phi, large_arc, sweep, x2, y2):
    if (x1, y1) == (x2, y2):
        return []
    if rx == 0 or ry == 0:
        return [((x1, y1), (x1, y1), (x2, y2), (x2, y2))]

    phi_rad = math.radians(phi)
    cos_phi = math.cos(phi_rad)
    sin_phi = math.sin(phi_rad)

    dx = (x1 - x2) / 2
    dy = (y1 - y2) / 2
    x1_prime = cos_phi * dx + sin_phi * dy
    y1_prime = -sin_phi * dx + cos_phi * dy

    lambda_ = (x1_prime / rx) ** 2 + (y1_prime / ry) ** 2
    if lambda_ > 1:
        rx *= math.sqrt(lambda_)
        ry *= math.sqrt(lambda_)

    sq = max(0, (rx * ry) ** 2 - (rx * y1_prime) ** 2 - (ry * x1_prime) ** 2)
    sq = math.sqrt(sq / ((rx * y1_prime) ** 2 + (ry * x1_prime) ** 2))

    if large_arc == sweep:
        sq = -sq

    cx_prime = sq * rx * y1_prime / ry
    cy_prime = -sq * ry * x1_prime / rx

    cx = cos_phi * cx_prime - sin_phi * cy_prime + (x1 + x2) / 2
    cy = sin_phi * cx_prime + cos_phi * cy_prime + (y1 + y2) / 2

    def angle_between(ux, uy, vx, vy):
        n = math.sqrt(ux * ux + uy * uy) * math.sqrt(vx * vx + vy * vy)
        c = (ux * vx + uy * vy) / n
        c = max(-1, min(1, c))
        angle = math.acos(c)
        if ux * vy - uy * vx < 0:
            angle = -angle
        return angle

    theta1 = angle_between(1, 0, (x1_prime - cx_prime) / rx, (y1_prime - cy_prime) / ry)
    dtheta = angle_between(
        (x1_prime - cx_prime) / rx, (y1_prime - cy_prime) / ry,
        (-x1_prime - cx_prime) / rx, (-y1_prime - cy_prime) / ry
    )

    if sweep == 0 and dtheta > 0:
        dtheta -= 2 * math.pi
    elif sweep == 1 and dtheta < 0:
        dtheta += 2 * math.pi

    segments = max(1, int(math.ceil(abs(dtheta) / (math.pi / 2))))
    delta = dtheta / segments

    beziers = []
    for i in range(segments):
        theta_start = theta1 + i * delta
        theta_end = theta_start + delta

        alpha = math.sin(delta) * (math.sqrt(4 + 3 * math.tan(delta / 2) ** 2) - 1) / 3

        cos_start = math.cos(theta_start)
        sin_start = math.sin(theta_start)
        cos_end = math.cos(theta_end)
        sin_end = math.sin(theta_end)

        q1x = cos_start
        q1y = sin_start
        q2x = cos_end
        q2y = sin_end

        cp1x = q1x - q1y * alpha
        cp1y = q1y + q1x * alpha
        cp2x = q2x + q2y * alpha
        cp2y = q2y - q2x * alpha

        def transform(x, y):
            x *= rx
            y *= ry
            nx = cos_phi * x - sin_phi * y
            ny = sin_phi * x + cos_phi * y
            return (nx + cx, ny + cy)

        p0 = transform(q1x, q1y)
        p1 = transform(cp1x, cp1y)
        p2 = transform(cp2x, cp2y)
        p3 = transform(q2x, q2y)

        beziers.append((p0, p1, p2, p3))

    return beziers


def distance(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.sqrt(dx * dx + dy * dy)


def cubic_bezier_point(p0, p1, p2, p3, t):
    mt = 1 - t
    mt2 = mt * mt
    mt3 = mt2 * mt
    t2 = t * t
    t3 = t2 * t

    x = mt3 * p0[0] + 3 * mt2 * t * p1[0] + 3 * mt * t2 * p2[0] + t3 * p3[0]
    y = mt3 * p0[1] + 3 * mt2 * t * p1[1] + 3 * mt * t2 * p2[1] + t3 * p3[1]

    return (x, y)


def quadratic_bezier_point(p0, p1, p2, t):
    mt = 1 - t
    mt2 = mt * mt
    t2 = t * t

    x = mt2 * p0[0] + 2 * mt * t * p1[0] + t2 * p2[0]
    y = mt2 * p0[1] + 2 * mt * t * p1[1] + t2 * p2[1]

    return (x, y)


def point_in_polygon(point, polygon):
    x, y = point
    n = len(polygon)
    inside = False

    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]

        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside

        p1x, p1y = p2x, p2y

    return inside


def perpendicular_distance(point, line_start, line_end):
    x0, y0 = point
    x1, y1 = line_start
    x2, y2 = line_end

    dx = x2 - x1
    dy = y2 - y1
    line_length_sq = dx * dx + dy * dy

    if line_length_sq == 0:
        return distance(point, line_start)

    numerator = abs(dy * x0 - dx * y0 + x2 * y1 - y2 * x1)
    return numerator / math.sqrt(line_length_sq)


def simplify_path_rdp(points, epsilon):
    if len(points) < 3:
        return points

    max_dist = 0.0
    max_index = 0

    for i in range(1, len(points) - 1):
        dist = perpendicular_distance(points[i], points[0], points[-1])
        if dist > max_dist:
            max_dist = dist
            max_index = i

    if max_dist > epsilon:
        left = simplify_path_rdp(points[:max_index + 1], epsilon)
        right = simplify_path_rdp(points[max_index:], epsilon)

        return left[:-1] + right
    else:
        return [points[0], points[-1]]


def simplify_closed_path(points, epsilon):
    if len(points) < 4:
        return points

    simplified = simplify_path_rdp(points, epsilon)

    if simplified[0] != points[0]:
        simplified.insert(0, points[0])

    return simplified


def segments_intersect(p1, p2, p3, p4):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

    if abs(denom) < 1e-10:
        return False, None

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

    if 0 < t < 1 and 0 < u < 1:
        ix = x1 + t * (x2 - x1)
        iy = y1 + t * (y2 - y1)
        return True, (ix, iy)

    return False, None


def remove_self_intersections(points, offset_distance, debug=False):
    if len(points) < 4:
        return points

    centroid_x = sum(p[0] for p in points) / len(points)
    centroid_y = sum(p[1] for p in points) / len(points)

    max_iterations = 100
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        found_intersection = False

        n = len(points)
        for i in range(n):
            if found_intersection:
                break

            p1 = points[i]
            p2 = points[(i + 1) % n]

            for j in range(i + 2, n):
                if j == (i + n - 1) % n:
                    continue

                p3 = points[j]
                p4 = points[(j + 1) % n]

                intersects, int_point = segments_intersect(p1, p2, p3, p4)

                if intersects:
                    if debug:
                        print(f"  Found intersection between segments {i}-{i+1} and {j}-{j+1}")
                        print(f"    Intersection point: {int_point}")

                    path_a = points[:i+1] + [int_point] + points[j+1:]
                    path_b = [int_point] + points[i+1:j+1]

                    def signed_area(pts):
                        if len(pts) < 3:
                            return 0.0
                        area = 0.0
                        for k in range(len(pts)):
                            x1, y1 = pts[k]
                            x2, y2 = pts[(k + 1) % len(pts)]
                            area += (x2 - x1) * (y2 + y1)
                        return area / 2.0

                    area_a = abs(signed_area(path_a))
                    area_b = abs(signed_area(path_b))

                    if debug:
                        print(f"    Path A area (without loop): {area_a:.3f}")
                        print(f"    Path B area (loop only): {area_b:.3f}")

                    if area_a >= area_b:
                        points = path_a
                        if debug:
                            print(f"    Keeping path A (larger/outer envelope)")
                    else:
                        points = path_b
                        if debug:
                            print(f"    Keeping path B (the loop was larger)")

                    found_intersection = True
                    break

        if not found_intersection:
            break

    if debug and iteration > 1:
        print(f"  Removed self-intersections in {iteration} iterations")

    if len(points) < 3:
        if debug:
            print(f"  WARNING: Ended with too few points ({len(points)}), this may indicate a problem")

    return points


def calculate_polygon_winding(points):
    signed_area = 0.0
    n = len(points)
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        signed_area += (x2 - x1) * (y2 + y1)

    return -1 if signed_area > 0 else 1


def calculate_perpendicular_offset(point, prev_point, next_point, offset_distance, polygon_winding, debug=False):
    e1x = point[0] - prev_point[0]
    e1y = point[1] - prev_point[1]
    e2x = next_point[0] - point[0]
    e2y = next_point[1] - point[1]

    if debug:
        print(f"    Edge vectors: e1=({e1x:.3f}, {e1y:.3f}), e2=({e2x:.3f}, {e2y:.3f})")

    len1 = math.sqrt(e1x * e1x + e1y * e1y)
    len2 = math.sqrt(e2x * e2x + e2y * e2y)

    if len1 > 0:
        e1x /= len1
        e1y /= len1
    if len2 > 0:
        e2x /= len2
        e2y /= len2

    if debug:
        print(f"    Normalized edges: e1=({e1x:.3f}, {e1y:.3f}), e2=({e2x:.3f}, {e2y:.3f})")

    tangent_x = e1x + e2x
    tangent_y = e1y + e2y

    tangent_len = math.sqrt(tangent_x * tangent_x + tangent_y * tangent_y)
    if tangent_len > 0:
        tangent_x /= tangent_len
        tangent_y /= tangent_len

    if debug:
        print(f"    Average tangent: ({tangent_x:.3f}, {tangent_y:.3f})")

    normal_x = tangent_y
    normal_y = -tangent_x

    if debug:
        print(f"    Normal (perpendicular to tangent, 90° CW): ({normal_x:.3f}, {normal_y:.3f})")

    offset_dir_x = normal_x
    offset_dir_y = normal_y

    if debug:
        print(f"    Offset direction (before flip): ({offset_dir_x:.3f}, {offset_dir_y:.3f})")
        print(f"    Global polygon winding: {'CCW' if polygon_winding > 0 else 'CW'}")

    should_flip = False
    if offset_distance > 0 and polygon_winding < 0:
        should_flip = True
    elif offset_distance < 0 and polygon_winding > 0:
        should_flip = True

    if should_flip:
        offset_dir_x = -offset_dir_x
        offset_dir_y = -offset_dir_y
        if debug:
            if offset_distance < 0:
                print(f"    Flipped for inward offset on CCW polygon: ({offset_dir_x:.3f}, {offset_dir_y:.3f})")
            else:
                print(f"    Flipped for outward offset on CW polygon: ({offset_dir_x:.3f}, {offset_dir_y:.3f})")

    dot_product = e1x * e2x + e1y * e2y
    dot_product = max(-1.0, min(1.0, dot_product))
    direction_angle = math.acos(dot_product)

    turn_angle = math.pi - direction_angle

    if debug:
        print(f"    Direction angle: {math.degrees(direction_angle):.1f}°, Turn angle: {math.degrees(turn_angle):.1f}°")

    if turn_angle > math.pi * 0.9:
        miter_limit = 1.0
    else:
        half_turn = turn_angle / 2
        if abs(math.sin(half_turn)) > 0.01:
            miter_limit = 1.0 / math.sin(half_turn)
            miter_limit = min(miter_limit, 2.0)
        else:
            miter_limit = 2.0

    if debug:
        print(f"    Miter limit: {miter_limit:.3f}")

    adjusted_distance = abs(offset_distance) * miter_limit
    offset_x = point[0] + offset_dir_x * adjusted_distance
    offset_y = point[1] + offset_dir_y * adjusted_distance

    if debug:
        print(f"    Adjusted distance: {adjusted_distance:.3f}")
        print(f"    Final offset point: ({offset_x:.3f}, {offset_y:.3f})")

    return (offset_x, offset_y)


def offset_path(subpath, offset_distance, precision=0.05, debug=False):
    try:
        try:
            from inkex import Path
            if isinstance(subpath, Path):
                subpath = list(subpath)
        except (ImportError, NameError):
            pass

        points = subpath_to_points(subpath, precision)

        if len(points) < 3:
            if debug:
                print(f"ERROR: Not enough points ({len(points)}) after approximation")
            return None

        if len(points) > 1:
            first = points[0]
            last = points[-1]
            dist = math.sqrt((last[0] - first[0])**2 + (last[1] - first[1])**2)
            if dist < 0.001:
                points = points[:-1]
                if debug:
                    print(f"Removed duplicate closing point (distance: {dist:.6f})")

        original_count = len(points)
        points = simplify_closed_path(points, epsilon=precision * 2)
        if debug:
            print(f"Pre-simplified from {original_count} to {len(points)} points")

        if len(points) < 3:
            if debug:
                print(f"ERROR: Not enough points ({len(points)}) after pre-simplification")
            return None

        polygon_winding = calculate_polygon_winding(points)

        if debug:
            print(f"\n=== OFFSET DEBUG ===")
            print(f"Original polygon ({len(points)} points after pre-simplification):")
            print(f"  First 10 points: {points[:10]}")
            print(f"  Last 5 points: {points[-5:]}")
            print(f"Offset distance: {offset_distance}")
            print(f"Precision: {precision}")
            print(f"Global polygon winding: {'CCW' if polygon_winding > 0 else 'CW'}")
            print(f"\nProcessing first 5 points to show edge vectors:")

        offset_points = []
        n = len(points)
        for i, point in enumerate(points):
            prev_point = points[(i - 1) % n]
            next_point = points[(i + 1) % n]

            offset_point = calculate_perpendicular_offset(point, prev_point, next_point, offset_distance, polygon_winding, debug=(debug and i < 5))

            if debug and i < 5:
                e1_dx = point[0] - prev_point[0]
                e1_dy = point[1] - prev_point[1]
                e2_dx = next_point[0] - point[0]
                e2_dy = next_point[1] - point[1]
                print(f"\n  Point [{i}]: {point}")
                print(f"    Prev point: {prev_point}")
                print(f"    Next point: {next_point}")
                print(f"    Edge 1 vector (from prev): ({e1_dx:.3f}, {e1_dy:.3f})")
                print(f"    Edge 2 vector (to next): ({e2_dx:.3f}, {e2_dy:.3f})")
                print(f"    Offset point: {offset_point}")
                print(f"    Movement: ({offset_point[0] - point[0]:.3f}, {offset_point[1] - point[1]:.3f})")

            if offset_point:
                offset_points.append(offset_point)

        if debug:
            print(f"\nResult:")
            print(f"  Offset points generated: {len(offset_points)}")
            print(f"  First 5 offset points: {offset_points[:5]}")
            print(f"  Last 5 offset points: {offset_points[-5:]}")

        if len(offset_points) < 3:
            if debug:
                print(f"ERROR: Not enough offset points ({len(offset_points)})")
            return None

        if debug:
            print(f"\nRemoving self-intersections...")
        cleaned_points = remove_self_intersections(offset_points, offset_distance, debug=debug)

        if debug:
            print(f"  Points after cleaning: {len(cleaned_points)}")
            if len(cleaned_points) != len(offset_points):
                print(f"  Removed {len(offset_points) - len(cleaned_points)} points from self-intersecting loops")

        simplified_points = simplify_closed_path(cleaned_points, epsilon=precision)

        if debug:
            print(f"\nSimplification:")
            print(f"  Cleaned offset points: {len(cleaned_points)}")
            print(f"  Simplified points: {len(simplified_points)}")
            print(f"  Reduction: {len(cleaned_points) - len(simplified_points)} points ({100 * (1 - len(simplified_points) / len(cleaned_points)):.1f}%)")

        offset_points = simplified_points

        path_str = f"M {offset_points[0][0]},{offset_points[0][1]}"
        for point in offset_points[1:]:
            path_str += f" L {point[0]},{point[1]}"
        path_str += " Z"

        if debug:
            print(f"  Path string (first 100 chars): {path_str[:100]}...")
            print(f"=== END DEBUG ===\n")

        try:
            from inkex import Path as InkexPath
            return InkexPath(path_str)
        except ImportError:
            result = [('M', offset_points[0])]
            for point in offset_points[1:]:
                result.append(('L', point))
            result.append(('Z', None))
            return result

    except Exception as e:
        print(f"Offset failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def offset_lpe(element, offset_distance, unit="mm"):
    lpe_str = (
        f"offset,"
        f"0,1,"
        f"offset:{offset_distance},"
        f"linejoin_type:miter,"
        f"miter_limit:4,"
        f"attempt_force_join:false,"
        f"update_on_knot_move:true;"
    )

    existing_lpe = element.get('inkscape:path-effect', '')
    if existing_lpe:
        new_lpe = existing_lpe + lpe_str
    else:
        new_lpe = lpe_str

    element.set('inkscape:path-effect', new_lpe)

    if not element.get('inkscape:original-d'):
        element.set('inkscape:original-d', element.get('d'))

    return element


def boolean_lpe(svg, element, operand_elements, operation="union"):
    if not operand_elements:
        return element

    defs = svg.defs
    if defs is None:
        from lxml import etree
        defs = etree.SubElement(svg.getroot(), 'defs')

    hidder_filter_id = "selectable_hidder_filter"
    hidder_filter = svg.getElementById(hidder_filter_id)
    if hidder_filter is None:
        from lxml import etree
        nsmap = {'inkscape': 'http://www.inkscape.org/namespaces/inkscape'}
        hidder_filter = etree.SubElement(defs, 'filter', {
            'id': hidder_filter_id,
            'width': '1',
            'height': '1',
            'x': '0',
            'y': '0',
            'style': 'color-interpolation-filters:sRGB;',
            '{http://www.inkscape.org/namespaces/inkscape}label': 'LPE boolean visibility'
        })
        fe_composite = etree.SubElement(hidder_filter, 'feComposite', {
            'id': 'boolops_hidder_primitive',
            'result': 'composite1',
            'operator': 'arithmetic',
            'in2': 'SourceGraphic',
            'in': 'BackgroundImage'
        })

    lpe_refs = []

    for operand in operand_elements:
        operand_id = operand.get('id')
        if not operand_id:
            continue

        lpe_id = svg.get_unique_id('path-effect')

        from lxml import etree
        path_effect = etree.SubElement(defs, '{http://www.inkscape.org/namespaces/inkscape}path-effect', {
            'effect': 'bool_op',
            'operand-path': f'#{operand_id}',
            'id': lpe_id,
            'is_visible': 'true',
            'lpeversion': '1',
            'operation': operation,
            'swap-operands': 'false',
            'filltype-this': 'from-curve',
            'filter': '',
            'filltype-operand': 'from-curve'
        })

        lpe_refs.append(f'#{lpe_id}')

        existing_style = operand.get('style', '')
        if 'filter:' not in existing_style:
            if existing_style and not existing_style.endswith(';'):
                existing_style += ';'
            operand.set('style', existing_style + f'filter:url(#{hidder_filter_id})')

    existing_lpe = element.get('{http://www.inkscape.org/namespaces/inkscape}path-effect', '')
    if existing_lpe:
        new_lpe = existing_lpe + ';' + ';'.join(lpe_refs)
    else:
        new_lpe = ';'.join(lpe_refs)

    element.set('{http://www.inkscape.org/namespaces/inkscape}path-effect', new_lpe)

    return element
