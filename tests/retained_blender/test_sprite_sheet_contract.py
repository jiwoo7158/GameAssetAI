"""Offline sprite-sheet contract, pixel placement and publication safety tests."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src" / "gameassetai" / "blender"))
from assemble_2d_sprite_sheet import (  # noqa: E402
    _decode_sheet_rgba8, assemble_2d_sprite_sheet)
from quantize_rgba import encode_png_rgba8  # noqa: E402
from validate_2d_sprite_sheet_request import (  # noqa: E402
    SPRITE_SHEET_SCHEMA, SPRITE_SHEET_SCHEMA_V1,
    validate_2d_sprite_sheet_request)


class SpriteSheetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gameassetai-spritesheet-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        colors = ((255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255))
        self.frames = []
        for index, color in enumerate(colors):
            path = self.root / f"frame-{index}.png"
            path.write_bytes(encode_png_rgba8([[color, color], [color, color]]))
            self.frames.append({"source_frame": index + 1, "sequence_index": index,
                                "path": str(path),
                                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                "anchor_pixel_from_bottom_left": [1, 1]})
        self.target = self.root / "sheet.png"
        self.metadata = self.root / "sheet.json"
        self.request = {
            "schema": SPRITE_SHEET_SCHEMA,
            "profile": {"name": None, "reference_sha256": None,
                        "profile_sha256": None, "preset_sha256": None},
            "frames": self.frames,
            "layout": {"cell_size": [2, 2], "columns": 2, "rows": 2,
                       "padding": 1, "order": "ROW_MAJOR_TOP_LEFT"},
            "output": {"target_file": str(self.target),
                       "metadata_file": str(self.metadata), "overwrite": False},
        }

    def test_preview_is_read_only_and_maps_explicit_cells(self):
        before = {path.name: path.read_bytes() for path in self.root.iterdir()}
        preview = validate_2d_sprite_sheet_request(self.request)
        self.assertEqual("ready", preview["status"])
        self.assertEqual([5, 5], preview["sheet_size"])
        self.assertEqual([[0, 0, 2, 2], [3, 0, 2, 2], [0, 3, 2, 2]],
                         [cell["rect_from_top_left"] for cell in preview["cells"]])
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.root.iterdir()})

    def test_assembly_places_pixels_and_binds_metadata(self):
        preview = validate_2d_sprite_sheet_request(self.request)
        result = assemble_2d_sprite_sheet(self.request, preview, authorize=True)
        self.assertEqual("created", result["status"])
        self.assertEqual(2, result["published_count"])
        _, pixels = _decode_sheet_rgba8(self.target)
        self.assertEqual((255, 0, 0, 255), pixels[0][0])
        self.assertEqual((0, 255, 0, 255), pixels[0][3])
        self.assertEqual((0, 0, 255, 255), pixels[3][0])
        self.assertEqual((0, 0, 0, 0), pixels[2][2])
        metadata = json.loads(self.metadata.read_text(encoding="utf-8"))
        self.assertEqual("gameassetai.2d-sprite-sheet-metadata.v2", metadata["schema"])
        self.assertEqual(self.request["profile"], metadata["profile"])
        self.assertEqual([1.0, 4.0], metadata["cells"][0]["anchor_in_sheet_from_bottom_left"])
        self.assertEqual(result["sheet_sha256"], metadata["image"]["sha256"])
        self.assertEqual([], list(self.root.glob(".gameassetai-spritesheet-*")))

    def test_authorization_and_stale_preview_refuse_without_writes(self):
        preview = validate_2d_sprite_sheet_request(self.request)
        self.assertEqual("error", assemble_2d_sprite_sheet(
            self.request, preview, authorize=False)["status"])
        stale = dict(preview); stale["request_sha256"] = "0" * 64
        self.assertEqual("error", assemble_2d_sprite_sheet(
            self.request, stale, authorize=True)["status"])
        self.assertFalse(self.target.exists())
        self.assertFalse(self.metadata.exists())

    def test_hash_dimension_layout_and_collision_refuse(self):
        changed = json.loads(json.dumps(self.request))
        changed["frames"][0]["sha256"] = "0" * 64
        self.assertEqual("error", validate_2d_sprite_sheet_request(changed)["status"])
        changed = json.loads(json.dumps(self.request))
        changed["layout"]["cell_size"] = [3, 2]
        self.assertEqual("error", validate_2d_sprite_sheet_request(changed)["status"])
        changed = json.loads(json.dumps(self.request))
        changed["layout"]["columns"] = changed["layout"]["rows"] = 1
        self.assertEqual("error", validate_2d_sprite_sheet_request(changed)["status"])
        changed = json.loads(json.dumps(self.request))
        changed["layout"].update(cell_size=[4096, 4096], columns=2, rows=2)
        self.assertEqual("error", validate_2d_sprite_sheet_request(changed)["status"])
        self.target.write_bytes(b"sentinel")
        self.assertEqual("error", validate_2d_sprite_sheet_request(self.request)["status"])
        self.assertEqual(b"sentinel", self.target.read_bytes())

    def test_partial_publication_is_rolled_back(self):
        preview = validate_2d_sprite_sheet_request(self.request)
        import assemble_2d_sprite_sheet as module
        real_link, calls = module.os.link, []

        def fail_second(source, target):
            calls.append(target)
            if len(calls) == 2:
                raise OSError("synthetic metadata publication failure")
            return real_link(source, target)

        with patch.object(module.os, "link", side_effect=fail_second):
            result = assemble_2d_sprite_sheet(self.request, preview, authorize=True)
        self.assertEqual("error", result["status"])
        self.assertEqual(0, result["published_count"])
        self.assertFalse(self.target.exists())
        self.assertFalse(self.metadata.exists())
        self.assertEqual([], list(self.root.glob(".gameassetai-spritesheet-*")))

    def test_order_indices_and_exact_fields_are_required(self):
        changed = json.loads(json.dumps(self.request))
        changed["layout"]["order"] = "COLUMN_MAJOR"
        self.assertEqual("error", validate_2d_sprite_sheet_request(changed)["status"])
        changed = json.loads(json.dumps(self.request))
        changed["frames"][0]["sequence_index"] = 9
        self.assertEqual("error", validate_2d_sprite_sheet_request(changed)["status"])
        changed = json.loads(json.dumps(self.request))
        changed["extra"] = True
        self.assertEqual("error", validate_2d_sprite_sheet_request(changed)["status"])

    def test_profile_provenance_is_all_or_nothing(self):
        changed = json.loads(json.dumps(self.request))
        changed["profile"] = {"name": "PixelGame", "reference_sha256": "1" * 64,
                              "profile_sha256": "2" * 64, "preset_sha256": "3" * 64}
        self.assertEqual("ready", validate_2d_sprite_sheet_request(changed)["status"])
        changed["profile"]["preset_sha256"] = None
        self.assertEqual("error", validate_2d_sprite_sheet_request(changed)["status"])

    def test_v1_request_remains_legacy_compatible(self):
        legacy = json.loads(json.dumps(self.request))
        legacy["schema"] = SPRITE_SHEET_SCHEMA_V1
        del legacy["profile"]
        preview = validate_2d_sprite_sheet_request(legacy)
        self.assertEqual("ready", preview["status"])
        result = assemble_2d_sprite_sheet(legacy, preview, authorize=True)
        self.assertEqual("created", result["status"])
        metadata = json.loads(self.metadata.read_text(encoding="utf-8"))
        self.assertEqual("gameassetai.2d-sprite-sheet-metadata.v1", metadata["schema"])
        self.assertNotIn("profile", metadata)


if __name__ == "__main__":
    unittest.main()
# Retained focused contract regression after the product restructure.
