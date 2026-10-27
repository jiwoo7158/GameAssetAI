"""Offline fixed-palette and PNG encoder regressions."""
from pathlib import Path
import struct
import sys
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from quantize_rgba import (apply_outer_outline_rgba8, encode_png_rgba8,
                           quantize_auto_rgba8, quantize_fixed_rgba8,
                           quantize_value_steps_rgba8)


class QuantizeRGBATests(unittest.TestCase):
    def test_nearest_color_tie_is_deterministic(self):
        pixels = [[(128, 0, 128, 255)]]
        palette = [[1, 0, 0, 1], [0, 0, 1, 1]]
        self.assertEqual([[(0, 0, 255, 255)]], quantize_fixed_rgba8(pixels, palette))

    def test_alpha_is_preserved_and_transparent_rgb_is_canonical(self):
        pixels = [[(99, 88, 77, 0), (250, 10, 10, 128)]]
        result = quantize_fixed_rgba8(pixels, [[1, 0, 0, 1]])
        self.assertEqual([[(0, 0, 0, 0), (255, 0, 0, 128)]], result)

    def test_duplicate_palette_colors_do_not_change_output(self):
        pixels = [[(10, 10, 10, 255), (240, 240, 240, 255)]]
        palette = [[0, 0, 0, 1], [1, 1, 1, 1], [0, 0, 0, 1]]
        self.assertEqual([[(0, 0, 0, 255), (255, 255, 255, 255)]],
                         quantize_fixed_rgba8(pixels, palette))

    def test_invalid_palette_and_pixels_refuse(self):
        for pixels, palette in (([], [[0, 0, 0, 1]]),
                                ([[(0, 0, 0, 255)], []], [[0, 0, 0, 1]]),
                                ([[(0, 0, 0, 256)]], [[0, 0, 0, 1]]),
                                ([[(0, 0, 0, 255)]], []),
                                ([[(0, 0, 0, 255)]], [[0, 0, 0, 0.5]])):
            with self.subTest(pixels=pixels, palette=palette):
                with self.assertRaises(ValueError):
                    quantize_fixed_rgba8(pixels, palette)

    def test_png_encoding_is_deterministic_and_structural(self):
        pixels = [[(0, 0, 0, 0), (255, 0, 0, 255)],
                  [(0, 255, 0, 255), (0, 0, 255, 255)]]
        first = encode_png_rgba8(pixels)
        self.assertEqual(first, encode_png_rgba8(pixels))
        self.assertEqual(b"\x89PNG\r\n\x1a\n", first[:8])
        self.assertEqual((2, 2, 8, 6), struct.unpack(">IIBB", first[16:26]))
        position, compressed = 8, []
        while position < len(first):
            length = struct.unpack(">I", first[position:position + 4])[0]
            kind = first[position + 4:position + 8]
            if kind == b"IDAT":
                compressed.append(first[position + 8:position + 8 + length])
            position += 12 + length
        self.assertEqual(18, len(zlib.decompress(b"".join(compressed))))

    def test_auto_palette_is_deterministic_and_bounded(self):
        pixels = [[(255, 0, 0, 255), (240, 10, 10, 255),
                   (0, 0, 255, 255), (10, 10, 240, 255)]]
        first, palette = quantize_auto_rgba8(pixels, 2)
        self.assertEqual((first, palette), quantize_auto_rgba8(pixels, 2))
        self.assertLessEqual(len(palette), 2)
        self.assertLessEqual(len({pixel[:3] for pixel in first[0]}), 2)

    def test_auto_palette_preserves_alpha_and_canonicalizes_transparent_rgb(self):
        result, palette = quantize_auto_rgba8(
            [[(90, 80, 70, 0), (30, 60, 90, 17), (200, 210, 220, 255)]], 2)
        self.assertEqual((0, 0, 0, 0), result[0][0])
        self.assertEqual([0, 17, 255], [pixel[3] for pixel in result[0]])
        self.assertTrue(all(color[3] == 255 for color in palette))

    def test_auto_palette_keeps_fewer_unique_colors_without_expansion(self):
        pixels = [[(10, 20, 30, 255), (40, 50, 60, 255)]]
        result, palette = quantize_auto_rgba8(pixels, 8)
        self.assertEqual(pixels, result)
        self.assertEqual([(10, 20, 30, 255), (40, 50, 60, 255)], palette)

    def test_auto_palette_refuses_invalid_or_invisible_input(self):
        for pixels, maximum in (([], 2), ([[(0, 0, 0, 0)]], 2),
                                ([[(0, 0, 0, 255)]], 1),
                                ([[(0, 0, 0, 256)]], 2)):
            with self.subTest(pixels=pixels, maximum=maximum):
                with self.assertRaises(ValueError):
                    quantize_auto_rgba8(pixels, maximum)

    def test_outer_outline_adds_only_one_eight_neighbor_ring(self):
        pixels = [[(0, 0, 0, 0) for _ in range(5)] for _ in range(5)]
        pixels[2][2] = (200, 100, 50, 128)
        result = apply_outer_outline_rgba8(pixels, [0, 0, 0, 1])
        self.assertEqual((200, 100, 50, 128), result[2][2])
        self.assertEqual(8, sum(pixel == (0, 0, 0, 255)
                                for row in result for pixel in row))
        self.assertEqual(0, result[0][0][3])

    def test_outer_outline_clips_at_canvas_and_refuses_bad_policy(self):
        pixels = [[(255, 0, 0, 255), (0, 0, 0, 0)],
                  [(0, 0, 0, 0), (0, 0, 0, 0)]]
        result = apply_outer_outline_rgba8(pixels, [0, 0, 1, 1])
        self.assertEqual(3, sum(pixel == (0, 0, 255, 255)
                                for row in result for pixel in row))
        with self.assertRaises(ValueError):
            apply_outer_outline_rgba8(pixels, [0, 0, 0, 1], width=2)

    def test_value_steps_band_value_preserve_alpha_and_rgb_ratios(self):
        pixels = [[(100, 50, 25, 128), (255, 128, 0, 255), (9, 8, 7, 0)]]
        result = quantize_value_steps_rgba8(pixels, 3)
        self.assertEqual((128, 64, 32, 128), result[0][0])
        self.assertEqual((255, 128, 0, 255), result[0][1])
        self.assertEqual((0, 0, 0, 0), result[0][2])
        self.assertLessEqual(len({max(pixel[:3]) for pixel in result[0]
                                  if pixel[3] > 0}), 3)

    def test_value_steps_are_deterministic_and_refuse_invalid_input(self):
        pixels = [[(64, 32, 16, 255), (192, 96, 48, 255)]]
        self.assertEqual(quantize_value_steps_rgba8(pixels, 4),
                         quantize_value_steps_rgba8(pixels, 4))
        for bad_pixels, steps in (([], 4), (pixels, 1), (pixels, 33),
                                  (pixels, True), ([[(0, 0, 0, 256)]], 4)):
            with self.subTest(pixels=bad_pixels, steps=steps):
                with self.assertRaises(ValueError):
                    quantize_value_steps_rgba8(bad_pixels, steps)


if __name__ == "__main__":
    unittest.main()
