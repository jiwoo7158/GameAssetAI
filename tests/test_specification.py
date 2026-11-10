from pathlib import Path
import copy
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gameassetai.errors import ValidationError  # noqa: E402
from gameassetai.specification import validate_asset_specification  # noqa: E402


def valid_spec():
    return {
        "schema": "gameassetai.asset-specification.v1",
        "asset_id": "forest-guardian",
        "name": "Forest Guardian",
        "game": "example-game",
        "operation": "create",
        "asset_type": "plant-creature",
        "description": "A readable plant creature based on direct concept references.",
        "style": {
            "three_d": "soft-chibi-cartoon-3d",
            "two_d": ["animated-sprite-sheet"],
            "overrides": {"palette": ["moss", "bark"]},
        },
        "references": [
            {"path": "D:/references/guardian-front.png", "role": "front", "sha256": None},
            {"path": "D:/references/guardian-side.png", "role": "side", "sha256": "a" * 64},
        ],
        "generation": {"provider": "auto", "options": {}},
        "source": None,
        "rig_animation": {"rig": "asset-specific", "actions": ["idle", "walk"]},
        "outputs": [{"format": "blend", "options": {}}, {"format": "sprite-sheet", "options": {}}],
    }


class SpecificationTests(unittest.TestCase):
    def test_nonhumanoid_specification_is_valid(self):
        result = validate_asset_specification(valid_spec(), ROOT / "catalog")
        self.assertEqual("plant-creature", result["asset_type"])
        self.assertEqual("asset-specific", result["rig_animation"]["rig"])

    def test_unknown_catalog_type_is_refused(self):
        document = valid_spec()
        document["asset_type"] = "new-python-module-per-noun"
        with self.assertRaises(ValidationError):
            validate_asset_specification(document, ROOT / "catalog")

    def test_modify_requires_preserved_source(self):
        document = valid_spec()
        document["operation"] = "modify"
        with self.assertRaisesRegex(ValidationError, "source"):
            validate_asset_specification(document, ROOT / "catalog")
        document["source"] = {"path": "D:/assets/tree.blend", "object": "Tree", "preserve_original": False}
        with self.assertRaisesRegex(ValidationError, "preserve_original"):
            validate_asset_specification(document, ROOT / "catalog")
        document["source"]["preserve_original"] = True
        validate_asset_specification(document, ROOT / "catalog")


if __name__ == "__main__":
    unittest.main()
