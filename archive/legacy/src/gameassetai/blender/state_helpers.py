"""Bounded native source state and file-wide dependency inspection."""
import bpy

def _loose_surface(mesh):
    return [{"positions": [list(mesh.vertices[i].co) for i in face.vertices],
             "uv": [[list(layer.data[i].uv) for i in face.loop_indices] for layer in mesh.uv_layers],
             "material": face.material_index, "smooth": face.use_smooth}
            for face in mesh.polygons]


def _loose_state(obj):
    mesh = obj.data
    return {"vertices": [list(v.co) for v in mesh.vertices],
            "edges": [list(e.vertices) for e in mesh.edges], "surface": _loose_surface(mesh),
            "materials": [m.name if m else None for m in mesh.materials],
            "uv_names": [layer.name for layer in mesh.uv_layers],
            "matrix": [list(row) for row in obj.matrix_world],
            "location": list(obj.location), "scale": list(obj.scale),
            "rotation_euler":list(obj.rotation_euler),"rotation_quaternion":list(obj.rotation_quaternion),
            "rotation_axis_angle":list(obj.rotation_axis_angle),
            "delta_location":list(obj.delta_location),"delta_scale":list(obj.delta_scale),
            "delta_rotation_euler":list(obj.delta_rotation_euler),
            "delta_rotation_quaternion":list(obj.delta_rotation_quaternion)}


def _loose_file_blockers():
    owners = set(bpy.data.user_map())
    owners.update(owner.node_tree for owner in list(owners)
                  if getattr(owner, "node_tree", None) is not None)
    blockers = []
    for owner in owners:
        animation = getattr(owner, "animation_data", None)
        pose = getattr(owner, "pose", None)
        if ((animation and (animation.action or len(animation.drivers) or len(animation.nla_tracks)))
                or len(getattr(owner, "constraints", ()))
                or (pose and any(len(b.constraints) for b in pose.bones))):
            blockers.append(owner.name_full)
    return sorted(blockers)
# Retained bounded Blender capability; product support remains evidence-scoped.
