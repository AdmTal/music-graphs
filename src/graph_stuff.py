import re
from collections import defaultdict, namedtuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from src.theme_stuff import Theme
from src.cache_stuff import get_cache_dir

LINE_WIDTH = 3

Draw = namedtuple(
    "Draw",
    "pen_color fill_color p_points b_points e_points",
)

LDraw = namedtuple(
    "LDraw",
    "font font_size pen_color text_x text_y text_w text_j text",
)


def points_to_pixels(points, dpi):
    pixels = points * (dpi / 72)  # 72 points per inch
    return pixels


class Graph:
    def __init__(self, pen_color, fill_color, polygon_points):
        self._pen_color = pen_color
        self._fill_color = fill_color
        self._polygon_points = polygon_points


def split_attributes(attr_string):
    attributes_dict = {}
    attr_lines = re.split(r",(?!\d)", attr_string)
    for attr_line in attr_lines:
        attrs = attr_line.replace('"', "")
        key, value = attrs.split("=")
        attributes_dict[key] = value
    return attributes_dict


def compact_dot_format(file_content):
    file_content = file_content.replace("\n\t", "")
    file_content = file_content.replace("{", "{\n")
    file_content = file_content.replace(";", ";\n")
    file_content = file_content.replace("	", "")
    file_content = file_content.replace("\n\n", "")
    file_content = file_content.replace("\\\n", "")
    file_content = file_content.replace("}", "")
    return file_content


def split_numbers(sequence, n):
    # Create a regex pattern for n numbers
    pattern = r"((?:\b\d+\b\s*){" + str(n) + r"})(.*)"
    match = re.match(pattern, sequence)
    return match.groups() if match else (sequence, "")


def array_chunk(lst, chunk_size):
    return [lst[i: i + chunk_size] for i in range(0, len(lst), chunk_size)]


def parse_draw(draw_string, dpi):
    rest = draw_string.strip()
    pen_color = None
    fill_color = None
    p_points = None
    b_points = None
    e_points = None
    while rest.strip():
        command, rest = rest[0], rest[2:]
        if command == "c":
            num, rest = int(rest[0]), rest[3:]
            pen_color, rest = rest[:num], rest[num + 1:]
            continue
        if command == "C":
            num, rest = int(rest[0]), rest[3:]
            fill_color, rest = rest[:num], rest[num + 1:]
            continue
        if command == "P":
            num, rest = int(rest[0]), rest[2:]
            p_points, rest = split_numbers(rest, num * 2)
            p_points = array_chunk([float(i) for i in p_points.split()], 2)
            continue
        if command == "e":
            e_points, rest = split_numbers(rest, 4)
            e_points = [float(i) for i in e_points.split()]
            continue
        if command == "B":
            num, rest = int(rest[0]), rest[2:]
            b_points, rest = split_numbers(rest, num)
            b_points = [float(i) for i in b_points.split()]
            continue

        raise Exception(rest)

    return Draw(
        fill_color=fill_color,
        pen_color=pen_color,
        p_points=[
            [points_to_pixels(i[0], dpi), points_to_pixels(i[1], dpi)] for i in p_points
        ]
        if p_points
        else None,
        b_points=[points_to_pixels(i, dpi) for i in b_points] if b_points else None,
        e_points=[points_to_pixels(i, dpi) for i in e_points] if e_points else None,
    )


def parse_ldraw(ldraw_string, dpi):
    rest = ldraw_string.strip()
    font = None
    font_size = None
    pen_color = None
    text_x = None
    text_y = None
    text_w = None
    text_j = None
    text = None

    while rest.strip():
        command, rest = rest[0], rest[2:]
        if command == "F":
            first_space = rest.find(" ")
            font_size, rest = int(rest[:first_space]), rest[first_space + 1:]
            first_space = rest.find(" ")
            num, rest = int(rest[:first_space]), rest[first_space:]
            font, rest = (
                rest[first_space: first_space + num],
                rest[first_space + num + 1:],
            )
            continue
        if command == "c":
            num, rest = int(rest[0]), rest[3:]
            pen_color, rest = rest[:num], rest[num + 1:]
            continue
        if command == "T":
            nums, text = rest.split("-")
            text_x, text_y, text_j, text_w, text_len = [float(i) for i in nums.split()]
            rest = ""
            continue

        raise Exception(f"command = {command}; rest = {rest}")

    return LDraw(
        font=font,
        font_size=font_size,
        pen_color=pen_color,
        text_x=points_to_pixels(text_x, dpi),
        text_y=points_to_pixels(text_y, dpi),
        text_w=points_to_pixels(text_w, dpi),
        text_j=text_j,
        text=text,
    )


def get_dimensions(points):
    x_values = [point[0] for point in points]
    y_values = [point[1] for point in points]

    width = max(x_values) - min(x_values)
    height = max(y_values) - min(y_values)

    return int(width), int(height)


def hex_to_rgb(hex_color):
    if not hex_color:
        return None
    if not isinstance(hex_color, str):
        return hex_color
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i: i + 2], 16) for i in (0, 2, 4))


def draw_ellipse(
        offsets,
        image,
        e_points,
        node_outline_color=None,
        node_fill_color=None,
        node_shadow_color=None,
        node_shadow_size=None,
        line_width=None,
):
    x0, y0, w, h = e_points

    x0 += offsets[0]
    y0 += offsets[1]

    bounding_box = [
        x0 - w,
        y0 - h,
        x0 + w,
        y0 + h,
    ]

    # Draw shadow if bg_fade and bg_fade_size are provided
    if node_shadow_color and node_shadow_size:
        # Calculate the size increase based on the percentage
        increase_w = w * node_shadow_size
        increase_h = h * node_shadow_size
        shadow_size = [
            x0 - w - increase_w,
            y0 - h - increase_h,
            x0 + w + increase_w,
            y0 + h + increase_h,
        ]

        # Create a temporary image for the shadow
        temp_image = Image.new("RGBA", image.size, (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_image)

        # Draw and blur the shadow ellipse
        temp_draw.ellipse(shadow_size, fill=node_shadow_color)
        blur_radius = int(max(increase_w, increase_h))  # Gaussian blur radius
        temp_image = temp_image.filter(ImageFilter.GaussianBlur(radius=blur_radius))

        # Merge shadow with the main image
        image.paste(temp_image, (0, 0), temp_image)

    draw = ImageDraw.Draw(image)

    # Draw the main ellipse
    draw.ellipse(
        bounding_box,
        outline=hex_to_rgb(node_outline_color) if node_outline_color else None,
        fill=hex_to_rgb(node_fill_color) if node_fill_color else None,
        width=line_width,
    )


def bezier_point(t, points):
    while len(points) > 1:
        points = [
            tuple((1 - t) * p0 + t * p1 for p0, p1 in zip(points[i], points[i + 1]))
            for i in range(len(points) - 1)
        ]
    return points[0]


def draw_bezier_curve(offsets, image, points, pen_color, line_width):
    draw = ImageDraw.Draw(image)
    # Split the points into pairs
    points = [points[i: i + 2] for i in range(0, len(points), 2)]
    points = [(c[0] + offsets[0], c[1] + offsets[1]) for c in points]

    # Split the curve into segments
    segments = 100
    curve = [bezier_point(t / segments, points) for t in range(segments + 1)]

    # Draw the segments
    for i in range(segments):
        pen_color = hex_to_rgb(pen_color)
        draw.line((curve[i], curve[i + 1]), fill=pen_color, width=line_width)


def hex_to_rgba(color, alpha):
    return (
        *int(color[1:], 16).to_bytes(3, "big"),
        alpha,
    )


def calculate_alpha(frame_number, total_frames):
    fade_in_end = total_frames * 0.1
    fade_out_start = total_frames * 0.5

    if frame_number < fade_in_end:
        # Fade in phase
        return int(255 * (frame_number / fade_in_end))
    elif frame_number <= fade_out_start:
        # Full opacity phase
        return 255
    else:
        # Fade out phase
        return int(
            255 * ((total_frames - frame_number) / (total_frames - fade_out_start))
        )


def draw_fading_bezier_curve(
        base_image,
        offsets,
        theme,
        points,
        frame_number,
        track,
        animation_len,
):
    # Create a new transparent image to draw the Bézier curve
    overlay_image = Image.new("RGBA", base_image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay_image)

    # Calculate alpha value for current frame
    alpha = calculate_alpha(frame_number, animation_len)

    # Split the points into pairs and apply offsets
    points = [points[i: i + 2] for i in range(0, len(points), 2)]
    points = [(c[0] + offsets[0], c[1] + offsets[1]) for c in points]

    # Split the curve into segments
    segments = 300 * len(points)
    curve = [bezier_point(t / segments, points) for t in range(segments + 1)]

    # Draw the border/shadow
    border_width = theme.chord_line_width(track) * 2
    border_rgba_color = hex_to_rgba(theme.chord_line_border_color(track), alpha)
    for i in range(segments):
        draw.line(
            (
                curve[i],
                curve[i + 1],
            ),
            fill=border_rgba_color,
            width=border_width,
        )
    overlay_image = overlay_image.filter(ImageFilter.GaussianBlur(radius=5))
    draw = ImageDraw.Draw(overlay_image)

    # Convert hex color to RGBA with alpha for main line
    rgba_color = hex_to_rgba(theme.chord_line_color(track), alpha)

    # Draw the main line with fading effect
    for i in range(segments):
        draw.line(
            (
                curve[i],
                curve[i + 1],
            ),
            fill=rgba_color,
            width=theme.chord_line_width(track),
        )

    # Composite the transparent overlay onto the base image
    return Image.alpha_composite(
        base_image.convert("RGBA"),
        overlay_image,
    )


def animate_bezier_point(
        base_image,
        offsets,
        theme,
        track,
        points,
        frame_number,
        animation_length_in_frames,
):
    overlay_image = Image.new(
        "RGBA",
        base_image.size,
        color=None,
    )
    draw = ImageDraw.Draw(overlay_image)

    x_offset, y_offset = offsets

    t = frame_number / animation_length_in_frames
    point = bezier_point(t, [points[i: i + 2] for i in range(0, len(points), 2)])
    point_center = (x_offset + point[0], y_offset + point[1])

    # Draw the 3D-looking circle
    for i in range(theme.ball_radius(track) // 2):
        # Calculate the color gradient based on the specified ball color
        draw.ellipse(
            [
                (point_center[0] - i, point_center[1] - i),
                (point_center[0] + i, point_center[1] + i),
            ],
            fill=theme.ball_color(track),
            outline=hex_to_rgb(theme.ball_stroke_color(track)),
            width=theme.ball_stroke_width(track),
        )

    blur_max = theme.ball_g_blur_max(track)
    if blur_max:
        blur_radius = min(
            animation_length_in_frames - frame_number, theme.ball_g_blur_max(track)
        )
        overlay_image = overlay_image.filter(
            ImageFilter.GaussianBlur(radius=blur_radius)
        )

    # Composite the transparent overlay onto the base image
    return Image.alpha_composite(
        base_image.convert("RGBA"),
        overlay_image,
    )


def animate_ellipsis_blur(
        base_image,
        points,
        frame_number,
        offsets,
        theme,
        track,
        animation_len,
        velocity,
):
    image = base_image.copy()
    draw = ImageDraw.Draw(image)

    x_offset, y_offset = offsets
    x0, y0, w, h = points
    x0 += x_offset
    y0 += y_offset

    # Calculate the increase in size
    w_increase = w * theme.note_increase_size(track) * (velocity / 127)
    h_increase = h * theme.note_increase_size(track) * (velocity / 127)

    # Define the bounding box with the increased size
    bounding_box = [
        x0 - w - w_increase / 2,
        y0 - h - h_increase / 2,
        x0 + w + w_increase / 2,
        y0 + h + h_increase / 2,
    ]

    # Draw the initial ellipse
    draw.ellipse(
        bounding_box,
        outline=hex_to_rgb(theme.note_color(track)),
        width=theme.note_stroke_width(track),
    )

    # Determine the blur radius for this frame
    blur_strength = (frame_number / animation_len) * velocity
    blur_radius = max(1, blur_strength)

    # Create a mask for the ellipse to constrain the blur effect
    mask = Image.new("L", image.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse(bounding_box, fill=255)

    # Apply the blur effect on the mask
    mask_blurred = mask.filter(ImageFilter.GaussianBlur(blur_radius))

    # Create a solid image for the blur color
    ellipse = Image.new("RGBA", image.size, hex_to_rgb(theme.note_color(track)))

    # Composite the blurred mask with the ellipse onto the base image
    image.paste(ellipse, mask=mask_blurred)

    return image


def draw_centered_text(
        offsets,
        image,
        text,
        x,
        y,
        font_path,
        font_size,
        color,
        outline_color,
        stroke_width,
):
    font = ImageFont.truetype(font_path, font_size)
    draw = ImageDraw.Draw(image)
    x += offsets[0]
    y += offsets[1]
    draw.text(
        (x, y),
        text,
        font=font,
        fill=hex_to_rgb(color),
        stroke_width=stroke_width,
        stroke_fill=hex_to_rgb(outline_color),
    )

    return image


def paste_center(host_image, image):
    host_width, host_height = host_image.size
    width, height = image.size
    x = (host_width - width) // 2
    y = (host_height - height) // 2
    host_image.paste(image, (x, y), image)


def parse_graph(
        graph,
        theme: Theme,
):
    temp_filename = f"{get_cache_dir()}/graph.gv"
    graph.filename = temp_filename
    graph.render(view=False)
    file_contents = open(f"{temp_filename}.xdot").read()

    lines = compact_dot_format(file_contents).split("\n")

    nodes = {}
    edges = defaultdict(dict)

    for line in lines[1:-1]:
        line_id, attributes = line.split("[")
        line_id = line_id.strip().replace('"', "")
        attributes = attributes.replace("];", "")

        attrs_dict = split_attributes(attributes)

        if line_id == "graph":
            draw = parse_draw(attrs_dict["_draw_"], theme.dpi)
            host_image = Image.new(
                "RGBA",
                (
                    theme.width,
                    theme.height,
                ),
                color=None,
            )

            # offsets
            host_width, host_height = host_image.size
            width, height = get_dimensions(draw.p_points)
            x = (host_width - width) // 2
            y = (host_height - height) // 2
            offsets = (x, y)

            graph_image = Image.new(
                "RGBA",
                (
                    theme.width,
                    theme.height,
                ),
                color=(0, 0, 0, 0),
            )

            if theme.background_image:
                bg_image = Image.open(theme.background_image).convert("RGBA")
                bg_image = bg_image.resize(
                    (theme.width, theme.height),
                    Image.Resampling.LANCZOS,
                )
                host_image.paste(bg_image, (0, 0))
            else:
                # Create a new white image if background_image is false
                bg_image = Image.new("RGBA", (theme.width, theme.height), "white")
                host_image.paste(bg_image, (0, 0))

        if "_draw_" in attrs_dict:
            draw = parse_draw(attrs_dict["_draw_"], theme.dpi)
            if draw.e_points:
                draw_ellipse(
                    offsets,
                    graph_image,
                    draw.e_points,
                    theme.node_outline_color,
                    theme.node_fill_color,
                    theme.node_shadow_color,
                    theme.node_shadow_size,
                    theme.graph_line_width,
                )
                nodes[line_id] = draw

            if draw.b_points:
                a, b = line_id.split(" -- ")
                edges[a][b] = draw
                edges[b][a] = draw
                if theme.show_lines:
                    draw_bezier_curve(
                        offsets,
                        graph_image,
                        draw.b_points,
                        draw.pen_color,
                        theme.graph_line_width,
                    )

        if "_ldraw_" in attrs_dict and not theme.hide_letters:
            ldraw = parse_ldraw(attrs_dict["_ldraw_"], theme.dpi)

            if len(ldraw.text) == 2:
                dx = theme.text_location_offsets.len_2.x
                dy = theme.text_location_offsets.len_2.y
            else:
                dx = theme.text_location_offsets.len_1.x
                dy = theme.text_location_offsets.len_1.y

            draw_centered_text(
                offsets,
                graph_image,
                ldraw.text,
                ldraw.text_x + dx,
                ldraw.text_y + dy,
                theme.font,
                theme.font_size,
                theme.node_text_color,
                theme.node_text_outline_color,
                theme.node_text_stroke_width,
            )

    paste_center(host_image, graph_image)

    return host_image, nodes, edges, offsets
