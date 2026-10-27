bl_info = {
    "name": "GameAssetAI",
    "author": "GameAssetAI",
    "version": (0, 1, 5),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > GameAssetAI",
    "description": "Blender-native setup and execution controls for GameAssetAI workflows",
    "category": "3D View",
}

from . import operators, panels, properties


def register():
    properties.register()
    operators.register()
    panels.register()


def unregister():
    panels.unregister()
    operators.unregister()
    properties.unregister()
