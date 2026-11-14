from pathlib import Path
import copy
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gameassetai.errors import ValidationError  # noqa: E402
from gameassetai.outputs import ARTIFACT_KINDS  # noqa: E402
from gameassetai.specification import (  # noqa: E402
    BUILTIN_REFERENCE_ROLES, OUTPUT_FORMAT_ARTIFACTS, OUTPUT_FORMATS,
    REFERENCE_ROLE_MAX_LENGTH, validate_asset_specification,
)


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

    def test_logical_output_formats_map_to_registrable_artifact_contracts(self):
        self.assertEqual(
            {"blend", "fbx", "png", "sprite-sheet", "png-sequence"},
            OUTPUT_FORMATS,
        )
        self.assertEqual(OUTPUT_FORMATS, set(OUTPUT_FORMAT_ARTIFACTS))
        for artifact_contracts in OUTPUT_FORMAT_ARTIFACTS.values():
            self.assertTrue(artifact_contracts)
            for kind, extensions in artifact_contracts.items():
                self.assertIn(kind, ARTIFACT_KINDS)
                self.assertTrue(extensions)
                self.assertTrue(extensions.issubset(ARTIFACT_KINDS[kind][1]))

        # Registrable artifacts are broader than requested generation formats. Supporting
        # a safe path for one does not claim that GameAssetAI can generate or export it.
        self.assertIn(".glb", ARTIFACT_KINDS["export"][1])
        self.assertNotIn("glb", OUTPUT_FORMATS)

    def test_existing_output_format_contract_remains_compatible(self):
        for output_format in sorted(OUTPUT_FORMATS):
            document = valid_spec()
            document["outputs"] = [{"format": output_format, "options": {}}]
            validate_asset_specification(document, ROOT / "catalog")
        document = valid_spec()
        document["outputs"] = [{"format": "glb", "options": {}}]
        with self.assertRaisesRegex(ValidationError, r"outputs\[0\]"):
            validate_asset_specification(document, ROOT / "catalog")

    def test_reference_roles_preserve_builtins_and_accept_portable_extensions(self):
        self.assertEqual(
            {"concept", "front", "side", "back", "three-quarter", "source"},
            set(BUILTIN_REFERENCE_ROLES),
        )
        for role in (*sorted(BUILTIN_REFERENCE_ROLES), "top", "bottom", "detail", "material", "silhouette"):
            with self.subTest(role=role):
                document = valid_spec()
                document["references"] = [
                    {"path": "D:/references/view.png", "role": role, "sha256": None},
                ]
                validate_asset_specification(document, ROOT / "catalog")

    def test_reference_roles_reject_invalid_or_path_like_values(self):
        invalid = (
            None,
            "",
            " ",
            "../front",
            "front/view",
            "front\\view",
            "C:-front",
            "UPPERCASE",
            "front\nside",
            "con",
            "a" * (REFERENCE_ROLE_MAX_LENGTH + 1),
        )
        for role in invalid:
            with self.subTest(role=role):
                document = valid_spec()
                document["references"] = [
                    {"path": "D:/references/view.png", "role": role, "sha256": None},
                ]
                with self.assertRaisesRegex(ValidationError, r"references\[0\]\.role"):
                    validate_asset_specification(document, ROOT / "catalog")


if __name__ == "__main__":
    unittest.main()
