"""Fresh-process proof that saved Blender preferences enable the installed Add-on."""
import json
from pathlib import Path

import bpy
import gameassetai


module_file = Path(gameassetai.__file__).resolve()
expected_parent = Path(bpy.utils.user_resource("SCRIPTS", path="addons", create=False)).resolve()
checks = {
    "enabled_in_preferences": "gameassetai" in bpy.context.preferences.addons,
    "loaded_from_user_addons": expected_parent in module_file.parents,
    "version_0_1_5": tuple(gameassetai.bl_info["version"]) == (0, 1, 5),
    "scene_property_registered": hasattr(bpy.types.Scene, "gameassetai"),
    "panel_registered": hasattr(bpy.types, "GAA_PT_pixel_pipeline"),
}
if not all(checks.values()):
    raise AssertionError(checks)
print(json.dumps({
    "status": "restart_survived",
    "checks": checks,
    "module_file": str(module_file),
    "blender_version": bpy.app.version_string,
}, sort_keys=True))
