"""Deterministic fixed-palette RGBA8 quantization and minimal PNG encoding."""
from __future__ import annotations

import struct
import zlib
from collections import Counter


def _rgba8_palette(palette):
    if not isinstance(palette, list) or not palette:
        raise ValueError("fixed palette must be a nonempty list")
    result = []
    for color in palette:
        if (not isinstance(color, list) or len(color) != 4
                or any(isinstance(value, bool) or not isinstance(value, (int, float))
                       or not 0.0 <= float(value) <= 1.0 for value in color)):
            raise ValueError("palette colors must be RGBA values in [0, 1]")
        converted = tuple(round(float(value) * 255.0) for value in color)
        if converted[3] != 255:
            raise ValueError("first fixed-palette implementation requires opaque colors")
        if converted not in result:
            result.append(converted)
    return result


def quantize_fixed_rgba8(pixels, palette):
    """Map visible RGB to the nearest fixed color while preserving every alpha byte."""
    colors = _rgba8_palette(palette)
    if not isinstance(pixels, list) or not pixels or not isinstance(pixels[0], list):
        raise ValueError("pixels must be a nonempty rectangular row list")
    width = len(pixels[0])
    if not width or any(not isinstance(row, list) or len(row) != width for row in pixels):
        raise ValueError("pixels must be rectangular")
    output = []
    for row in pixels:
        mapped = []
        for pixel in row:
            if (not isinstance(pixel, (list, tuple)) or len(pixel) != 4
                    or any(isinstance(value, bool) or not isinstance(value, int)
                           or not 0 <= value <= 255 for value in pixel)):
                raise ValueError("pixels must contain RGBA8 values")
            red, green, blue, alpha = pixel
            if alpha == 0:
                mapped.append((0, 0, 0, 0))
                continue
            nearest = min(colors, key=lambda color: (
                (red - color[0]) ** 2 + (green - color[1]) ** 2
                + (blue - color[2]) ** 2, color))
            mapped.append((nearest[0], nearest[1], nearest[2], alpha))
        output.append(mapped)
    return output


def quantize_auto_rgba8(pixels, max_colors):
    """Deterministic weighted median-cut RGB reduction while preserving alpha bytes."""
    if isinstance(max_colors, bool) or not isinstance(max_colors, int) or not 2 <= max_colors <= 256:
        raise ValueError("max_colors must be an integer in [2, 256]")
    if not isinstance(pixels, list) or not pixels or not isinstance(pixels[0], list):
        raise ValueError("pixels must be a nonempty rectangular row list")
    width = len(pixels[0])
    if not width or any(not isinstance(row, list) or len(row) != width for row in pixels):
        raise ValueError("pixels must be rectangular")
    counts = Counter()
    for row in pixels:
        for pixel in row:
            if (not isinstance(pixel, (list, tuple)) or len(pixel) != 4
                    or any(isinstance(value, bool) or not isinstance(value, int)
                           or not 0 <= value <= 255 for value in pixel)):
                raise ValueError("pixels must contain RGBA8 values")
            if pixel[3] > 0:
                counts[tuple(pixel[:3])] += 1
    if not counts:
        raise ValueError("automatic palette requires at least one visible pixel")

    boxes = [sorted(counts)]
    while len(boxes) < min(max_colors, len(counts)):
        candidates = []
        for index, colors in enumerate(boxes):
            ranges = tuple(max(color[channel] for color in colors)
                           - min(color[channel] for color in colors) for channel in range(3))
            if len(colors) > 1:
                candidates.append((max(ranges), sum(counts[color] for color in colors),
                                   len(colors), tuple(colors), index, ranges))
        if not candidates:
            break
        _, _, _, _, index, ranges = max(candidates)
        colors = boxes.pop(index)
        channel = min(i for i, value in enumerate(ranges) if value == max(ranges))
        ordered = sorted(colors, key=lambda color: (color[channel], color))
        total, cumulative, cut = sum(counts[color] for color in ordered), 0, 1
        for position, color in enumerate(ordered[:-1], 1):
            cumulative += counts[color]
            cut = position
            if cumulative * 2 >= total:
                break
        boxes.extend((ordered[:cut], ordered[cut:]))

    palette = []
    for colors in boxes:
        weight = sum(counts[color] for color in colors)
        rgb = tuple((sum(color[channel] * counts[color] for color in colors)
                     + weight // 2) // weight for channel in range(3))
        palette.append((*rgb, 255))
    palette.sort()
    output = []
    for row in pixels:
        mapped = []
        for red, green, blue, alpha in row:
            if alpha == 0:
                mapped.append((0, 0, 0, 0))
                continue
            nearest = min(palette, key=lambda color: (
                (red - color[0]) ** 2 + (green - color[1]) ** 2
                + (blue - color[2]) ** 2, color))
            mapped.append((nearest[0], nearest[1], nearest[2], alpha))
        output.append(mapped)
    return output, palette


def quantize_value_steps_rgba8(pixels, value_steps):
    """Band HSV value into explicit equal steps while preserving alpha and RGB ratios."""
    if (isinstance(value_steps, bool) or not isinstance(value_steps, int)
            or not 2 <= value_steps <= 32):
        raise ValueError("value_steps must be an integer in [2, 32]")
    if not isinstance(pixels, list) or not pixels or not isinstance(pixels[0], list):
        raise ValueError("pixels must be a nonempty rectangular row list")
    width = len(pixels[0])
    if not width or any(not isinstance(row, list) or len(row) != width for row in pixels):
        raise ValueError("pixels must be rectangular")
    output = []
    denominator = value_steps - 1
    for row in pixels:
        mapped = []
        for pixel in row:
            if (not isinstance(pixel, (list, tuple)) or len(pixel) != 4
                    or any(isinstance(value, bool) or not isinstance(value, int)
                           or not 0 <= value <= 255 for value in pixel)):
                raise ValueError("pixels must contain RGBA8 values")
            red, green, blue, alpha = pixel
            if alpha == 0:
                mapped.append((0, 0, 0, 0))
                continue
            value = max(red, green, blue)
            if value == 0:
                mapped.append((0, 0, 0, alpha))
                continue
            band = (value * denominator + 127) // 255
            quantized_value = (band * 255 + denominator // 2) // denominator
            mapped.append(tuple((channel * quantized_value + value // 2) // value
                                for channel in (red, green, blue)) + (alpha,))
        output.append(mapped)
    return output


def apply_outer_outline_rgba8(pixels, color, width=1):
    """Paint one opaque 8-neighbor outer ring without changing source-visible pixels."""
    if width != 1:
        raise ValueError("first outline implementation requires width 1")
    outline = _rgba8_palette([color])[0]
    if not isinstance(pixels, list) or not pixels or not isinstance(pixels[0], list):
        raise ValueError("pixels must be a nonempty rectangular row list")
    height, row_width = len(pixels), len(pixels[0])
    if not row_width or any(not isinstance(row, list) or len(row) != row_width for row in pixels):
        raise ValueError("pixels must be rectangular")
    for row in pixels:
        for pixel in row:
            if (not isinstance(pixel, (list, tuple)) or len(pixel) != 4
                    or any(isinstance(value, bool) or not isinstance(value, int)
                           or not 0 <= value <= 255 for value in pixel)):
                raise ValueError("pixels must contain RGBA8 values")
    output = [[tuple(pixel) for pixel in row] for row in pixels]
    for y in range(height):
        for x in range(row_width):
            if pixels[y][x][3] != 0:
                continue
            if any(pixels[ny][nx][3] > 0
                   for ny in range(max(0, y - 1), min(height, y + 2))
                   for nx in range(max(0, x - 1), min(row_width, x + 2))
                   if (nx, ny) != (x, y)):
                output[y][x] = outline
    return output


def encode_png_rgba8(pixels):
    """Encode rectangular RGBA8 rows as a non-interlaced PNG with filter type 0."""
    if not isinstance(pixels, list) or not pixels or not isinstance(pixels[0], list):
        raise ValueError("pixels must be a nonempty rectangular row list")
    width, height = len(pixels[0]), len(pixels)
    rows = bytearray()
    for row in pixels:
        if not isinstance(row, list) or len(row) != width:
            raise ValueError("pixels must be rectangular")
        rows.append(0)
        for pixel in row:
            if (not isinstance(pixel, (list, tuple)) or len(pixel) != 4
                    or any(isinstance(value, bool) or not isinstance(value, int)
                           or not 0 <= value <= 255 for value in pixel)):
                raise ValueError("pixels must contain RGBA8 values")
            rows.extend(pixel)

    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xffffffff)

    signature = b"\x89PNG\r\n\x1a\n"
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return signature + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(bytes(rows), 9)) + chunk(b"IEND", b"")
# Retained bounded Blender capability; product support remains evidence-scoped.
