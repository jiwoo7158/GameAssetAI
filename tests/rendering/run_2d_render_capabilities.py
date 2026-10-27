"""Validate read-only 2D render capability inventory inside Blender."""


def run_2d_render_capability_tests():
    checks = []

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    report = inspect_2d_render_capabilities()
    check("status_ok", report["status"] == "ok")
    check("state_preserved", report["preserved"])
    check("png_available", "PNG" in report["image_output"]["file_formats"])
    check("rgba_available", "RGBA" in report["image_output"]["color_modes"])
    check("orthographic_camera", "ORTHO" in report["camera"]["types"] and
          report["camera"]["orthographic_scale_property"])
    check("resolution_controls", report["render"]["resolution_properties"])
    check("transparent_background", report["render"]["transparent_background_property"])
    check("image_save_apis", report["image_output"]["image_save"] and
          report["image_output"]["image_save_render"])
    check("compositor_core_types",
          (report["compositor"]["scene_node_tree_property"] or
           report["compositor"]["scene_compositing_node_group_property"]) and
          all(report["compositor"]["node_types"][name] for name in
              ("CompositorNodeRLayers", "CompositorNodeScale", "CompositorNodePixelate",
               "CompositorNodeOutputFile")))
    check("color_management", bool(report["color_management"]["view_transform"]) and
          report["color_management"]["exposure_property"] and
          report["color_management"]["gamma_property"])
    return {"status": "passed", "check_count": len(checks), "checks": checks,
            "capabilities": report, "blender_version": bpy.app.version_string}
