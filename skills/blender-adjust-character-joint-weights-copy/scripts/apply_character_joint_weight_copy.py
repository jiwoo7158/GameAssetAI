import hashlib
import json
import uuid

import bpy

from preview_character_joint_weight_copy import (_plan, _sha, _source_facts,
                                                  preview_character_joint_weight_copy)


OWNER_KEY = "gameassetai_joint_weight_copy_owner"


def apply_character_joint_weight_copy(request, *, expected_request_sha256,
                                      expected_source_fingerprint, expected_setup_fingerprint,
                                      expected_preview_fingerprint, authorized=False):
    report = {"status": "error", "errors": [], "published": False,
              "failure_cleanup": None, "receipt_fingerprint": None}
    created_object = created_mesh = None
    token = uuid.uuid4().hex
    try:
        if authorized is not True:
            raise ValueError("explicit apply authorization=true is required")
        expected = {"request_sha256": expected_request_sha256,
                    "source_fingerprint": expected_source_fingerprint,
                    "setup_fingerprint": expected_setup_fingerprint,
                    "preview_fingerprint": expected_preview_fingerprint}
        if any(not isinstance(value, str) or len(value) != 64 for value in expected.values()):
            raise ValueError("all expected fingerprints must be exact SHA-256 values")
        fresh = preview_character_joint_weight_copy(request, expected_request_sha256)
        if fresh["status"] != "candidate_for_review" or fresh["errors"] or fresh["blockers"]:
            raise ValueError("fresh blocker-free preview is required")
        for key, value in expected.items():
            if fresh[key] != value: raise ValueError(key + " changed since review")
        scene = bpy.data.scenes[request["scene_name"]]
        source = scene.objects[request["source_object_name"]]
        arm = scene.objects[request["armature_object_name"]]
        source_before = _source_facts(source, arm)
        character = json.loads(source["gameassetai_character_request"])
        plan = _plan(source, request, character["proportions"])
        created_mesh = source.data.copy(); created_mesh.name = request["output_mesh_name"]
        created_object = source.copy(); created_object.name = request["output_object_name"]
        created_object.data = created_mesh
        created_object[OWNER_KEY] = token; created_mesh[OWNER_KEY] = token
        collection = next((c for c in source.users_collection if c.name in scene.collection.children),
                          source.users_collection[0] if source.users_collection else scene.collection)
        collection.objects.link(created_object)
        for item in plan["changes"]:
            for name, weight in zip((item["first"], item["second"]), item["new"]):
                group = created_object.vertex_groups.get(name)
                if group is None: raise ValueError("target group disappeared during apply: " + name)
                group.add([item["vertex"]], weight, "REPLACE")
        if _sha([[float(x) for x in v.co] for v in created_mesh.vertices]) != _sha(source_before["geometry"]):
            raise ValueError("output geometry changed")
        if _sha(_source_facts(source, arm)) != _sha(source_before):
            raise ValueError("source changed during apply")
        receipt = {"request_sha256": fresh["request_sha256"],
                   "source_fingerprint": fresh["source_fingerprint"],
                   "setup_fingerprint": fresh["setup_fingerprint"],
                   "preview_fingerprint": fresh["preview_fingerprint"],
                   "source_object_name": source.name, "source_preserved": True,
                   "output_object_name": created_object.name, "output_mesh_name": created_mesh.name,
                   "armature_object_name": arm.name,
                   "adjustment": request["adjustment"],
                   "metrics": fresh["adjustment_preview"]}
        report.update({"status": "created", "published": True, "failure_cleanup": "not_needed",
                       "source_preserved": True, "output_independent": True,
                       "output": {"object_name": created_object.name, "mesh_name": created_mesh.name},
                       "metrics": fresh["adjustment_preview"],
                       "receipt_fingerprint": _sha(receipt)})
    except (ValueError, TypeError, KeyError, RuntimeError, json.JSONDecodeError) as exc:
        report["errors"].append(str(exc))
        try:
            if created_object and bpy.data.objects.get(created_object.name) is created_object:
                if created_object.get(OWNER_KEY) != token: raise RuntimeError("output ownership changed")
                bpy.data.objects.remove(created_object, do_unlink=True)
            if created_mesh and bpy.data.meshes.get(created_mesh.name) is created_mesh:
                if created_mesh.get(OWNER_KEY) != token or created_mesh.users != 0:
                    raise RuntimeError("output Mesh ownership/users changed")
                bpy.data.meshes.remove(created_mesh)
            report["failure_cleanup"] = "complete"
        except RuntimeError as cleanup:
            report["failure_cleanup"] = "unverified"; report["errors"].append(str(cleanup))
    return report
