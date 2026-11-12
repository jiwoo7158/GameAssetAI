import bpy


def _armature_poll(_settings, obj):
    return obj is not None and obj.type == "ARMATURE"


class GameAssetAISettings(bpy.types.PropertyGroup):
    resolution_x: bpy.props.IntProperty(name="Width", default=64, min=8, max=4096)
    resolution_y: bpy.props.IntProperty(name="Height", default=64, min=8, max=4096)
    framing_margin: bpy.props.FloatProperty(
        name="Framing Margin", default=0.1, min=0.0, max=1.0, subtype="FACTOR"
    )
    view_preset: bpy.props.EnumProperty(
        name="View",
        items=(
            ("FRONT", "Front", "Look from negative Y toward the target"),
            ("SIDE", "Side", "Look from positive X toward the target"),
            ("QUARTER", "Quarter", "Elevated three-quarter view"),
            ("TOP", "Top", "Look down from positive Z"),
        ),
        default="FRONT",
    )
    key_energy: bpy.props.FloatProperty(name="Key Energy", default=800.0, min=0.0)
    fill_energy: bpy.props.FloatProperty(name="Fill Energy", default=250.0, min=0.0)
    pixel_scale: bpy.props.IntProperty(
        name="Pixel Scale",
        description="Render-size divisor used by the compositor before nearest pixel expansion",
        default=4,
        min=1,
        max=64,
    )
    animation_armature: bpy.props.PointerProperty(
        name="Armature",
        type=bpy.types.Object,
        poll=_armature_poll,
    )
    animation_action: bpy.props.PointerProperty(
        name="Action",
        type=bpy.types.Action,
    )
    material_target: bpy.props.PointerProperty(
        name="Target Mesh",
        type=bpy.types.Object,
        poll=lambda _settings, obj: obj is not None and obj.type == "MESH",
    )
    material_preset: bpy.props.EnumProperty(
        name="Preset",
        items=(
            ("FLAT_LIT", "Flat Lit", "Constant-color rough Principled material"),
            ("CEL_BANDED", "Cel Banded", "EEVEE lighting reduced to discrete shadow bands"),
            ("EMISSION_UNLIT", "Emission Unlit", "Constant-color unlit emission material"),
        ),
        default="CEL_BANDED",
    )
    shadow_bands: bpy.props.IntProperty(
        name="Shadow Bands",
        default=3,
        min=2,
        max=6,
    )
    export_file: bpy.props.StringProperty(
        name="PNG File",
        subtype="FILE_PATH",
        default="",
    )
    preset_file: bpy.props.StringProperty(
        name="Preset JSON",
        subtype="FILE_PATH",
        default="",
    )
    sequence_helper_root: bpy.props.StringProperty(
        name="Sequence Helper Scripts",
        subtype="DIR_PATH",
        default="",
    )
    sequence_output_directory: bpy.props.StringProperty(
        name="Output Directory",
        subtype="DIR_PATH",
        default="",
    )
    sequence_prefix: bpy.props.StringProperty(name="Filename Prefix", default="frame-")
    sequence_frame_step: bpy.props.IntProperty(name="Frame Step", default=1, min=1, max=1024)
    sequence_index_padding: bpy.props.IntProperty(name="Index Padding", default=4, min=1, max=8)
    sprite_sheet_helper_root: bpy.props.StringProperty(
        name="Sprite Sheet Helper Scripts",
        subtype="DIR_PATH",
        default="",
    )
    sprite_sheet_file: bpy.props.StringProperty(name="Sheet PNG", subtype="FILE_PATH", default="")
    sprite_sheet_metadata_file: bpy.props.StringProperty(
        name="Cell Metadata JSON", subtype="FILE_PATH", default=""
    )
    sprite_sheet_columns: bpy.props.IntProperty(name="Columns", default=4, min=1, max=2048)
    sprite_sheet_rows: bpy.props.IntProperty(name="Rows", default=2, min=1, max=2048)
    sprite_sheet_padding: bpy.props.IntProperty(name="Padding", default=0, min=0, max=256)


CLASSES = (GameAssetAISettings,)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.gameassetai = bpy.props.PointerProperty(type=GameAssetAISettings)


def unregister():
    if hasattr(bpy.types.Scene, "gameassetai"):
        del bpy.types.Scene.gameassetai
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
