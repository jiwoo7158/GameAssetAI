from pathlib import Path
import json
import shutil
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gameassetai.catalog import load_registry, validate_catalog  # noqa: E402


class CatalogTests(unittest.TestCase):
    def test_product_catalogs_validate_and_separate_status(self):
        report = validate_catalog(ROOT / "catalog")
        self.assertEqual("valid", report["status"])
        self.assertGreaterEqual(report["registries"]["asset-types"]["entries"], 30)
        asset = load_registry(ROOT / "catalog", "asset-types").get("monster-creature")
        self.assertEqual("registered", asset["catalog_status"])
        self.assertEqual("not-implemented", asset["implementation_status"])
        self.assertEqual("none", asset["evidence"])

    def test_new_asset_child_is_data_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            catalog = Path(temporary) / "catalog"
            shutil.copytree(ROOT / "catalog", catalog)
            custom = {
                "schema": "gameassetai.asset-types.v1",
                "asset_types": [{
                    "id": "fox-like-animal", "label": "Fox-like Animal",
                    "description": "Example extension sharing an animal production provider.",
                    "category": "character", "parent": "animal-wildlife",
                    "catalog_status": "registered", "implementation_status": "not-implemented",
                    "evidence": "none", "dynamic": True, "rig_policy": "asset-specific",
                }],
            }
            (catalog / "asset-types" / "custom.json").write_text(
                json.dumps(custom), encoding="utf-8",
            )
            registry = load_registry(catalog, "asset-types")
            self.assertIn("fox-like-animal", registry.entries)
            self.assertEqual("animal-wildlife", registry.get("fox-like-animal")["parent"])

    def test_unadopted_generation_providers_do_not_claim_implementation_or_evidence(self):
        providers = load_registry(ROOT / "catalog", "generation-providers")
        for identifier in (
            "blender-native", "procedural-python", "existing-asset-revision",
        ):
            with self.subTest(provider=identifier):
                provider = providers.get(identifier)
                self.assertEqual("registered", provider["catalog_status"])
                self.assertEqual("not-implemented", provider["implementation_status"])
                self.assertEqual("none", provider["evidence"])

    def test_archived_blender_evidence_does_not_promote_catalog_entries(self):
        assets = load_registry(ROOT / "catalog", "asset-types")
        styles = load_registry(ROOT / "catalog", "styles")
        for identifier in (
            "humanoid-character",
            "weapon",
            "shield",
            "tool",
            "furniture",
            "container-storage",
            "general-prop",
            "architectural-module",
            "dungeon-module",
        ):
            with self.subTest(asset_type=identifier):
                entry = assets.get(identifier)
                self.assertEqual("registered", entry["catalog_status"])
                self.assertEqual("not-implemented", entry["implementation_status"])
                self.assertEqual("none", entry["evidence"])
        sprite = styles.get("animated-sprite-sheet")
        self.assertEqual("registered", sprite["catalog_status"])
        self.assertEqual("not-implemented", sprite["implementation_status"])
        self.assertEqual("none", sprite["evidence"])


if __name__ == "__main__":
    unittest.main()
