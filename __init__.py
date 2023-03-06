bl_info = {
    "name": "VertexGroup Renamer",
    "author": "takec",
    "version": (1, 1),
    "blender": (3, 4, 0),
    "location": "View3D > Tool Shelf > Renamer > VertexGroup Renamer",
    "description": "Renames vertex groups based on bone mappings",
    "category": "Object"
}

import bpy
from bpy_extras.io_utils import ImportHelper, ExportHelper
import csv

class MappingPairProperty(bpy.types.PropertyGroup):
    src: bpy.props.StringProperty(name="src")
    dst: bpy.props.StringProperty(name="dst")

class VertexGroupRenamerProperties(bpy.types.PropertyGroup):
    armature_source: bpy.props.PointerProperty(
        name="src",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == "ARMATURE",
    )
    armature_target: bpy.props.PointerProperty(
        name="trg",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == "ARMATURE",
    )
    bone_max_distance: bpy.props.FloatProperty(
        name="max distance",
        default=1.0,
        min=0,
        step=1,
        precision=6,
        unit="LENGTH",
    )
    mapping_collection: bpy.props.CollectionProperty(
        type=MappingPairProperty,
        )
    mapping_active_index: bpy.props.IntProperty()

class VERTEX_GROUP_RENAMER_UL_MappingPair(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        enable = (flt_flag & self.bitflag_filter_item)
        if self.use_filter_invert:
            enable = not enable
        if enable:
            layout.prop(item, "src", text="", emboss=False, translate=False)
            layout.prop(item, "dst", text="", emboss=False, translate=False)
    
    # def draw_filter(self, context, layout):
    #     pass

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        flt_flags = []
        flt_neworder = []

        if self.filter_name:
            flt_flags = bpy.types.UI_UL_list.filter_items_by_name(self.filter_name, self.bitflag_filter_item, items, "src")
        else:
            flt_flags = [self.bitflag_filter_item] * len(items)
        
        if self.use_filter_sort_alpha:
            flt_neworder = bpy.types.UI_UL_list.sort_items_by_name(items, "src")

        return flt_flags, flt_neworder

class VERTEX_GROUP_RENAMER_OT_MappingCollection_Add(bpy.types.Operator):
    bl_idname = "vertex_group_renamer.mapping_collection_add"
    bl_label = "add mapping_pair to collection"
    def execute(self, context):
        context.scene.VertexGroupRenamerProperty.mapping_collection.add()
        return {"FINISHED"}

class VERTEX_GROUP_RENAMER_OT_MappingCollection_Remove(bpy.types.Operator):
    bl_idname = "vertex_group_renamer.mapping_collection_remove"
    bl_label = "remove mapping_pair from collection"
    def execute(self, context):
        props = context.scene.VertexGroupRenamerProperty
        mapping_collection = props.mapping_collection
        active_index = props.mapping_active_index
        mapping_collection.remove(active_index)
        active_index = min(active_index, len(mapping_collection)-1)
        return {"FINISHED"}

class VERTEX_GROUP_RENAMER_OT_MappingCollection_Clear(bpy.types.Operator):
    bl_idname = "vertex_group_renamer.mapping_collection_clear"
    bl_label = "clear mapping collection"
    def execute(self, context):
        props = context.scene.VertexGroupRenamerProperty
        mapping_collection = props.mapping_collection
        mapping_collection.clear()
        return {"FINISHED"}

class VERTEX_GROUP_RENAMER_OT_MappingCollection_Import(bpy.types.Operator, ImportHelper):
    bl_idname = "vertex_group_renamer.mapping_collection_import"
    bl_label = "import mapping from csv"
    filter_glob: bpy.props.StringProperty(
        default="*.csv",
        options={"HIDDEN"},
    )
    def execute(self, context):
        props = context.scene.VertexGroupRenamerProperty
        mapping_collection = props.mapping_collection
        mapping_collection.clear()
        with open(self.filepath, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                pair = mapping_collection.add()
                pair.src = row[0]
                pair.dst = row[1]
        return {"FINISHED"}

class VERTEX_GROUP_RENAMER_OT_MappingCollection_Export(bpy.types.Operator, ExportHelper):
    bl_idname = "vertex_group_renamer.mapping_collection_export"
    bl_label = "export mapping to csv"
    filename_ext = ".csv"
    filter_glob: bpy.props.StringProperty(
        default="*.csv",
        options={"HIDDEN"},
    )
    def execute(self, context):
        props = context.scene.VertexGroupRenamerProperty
        mapping_collection = props.mapping_collection
        with open(self.filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            for pair in mapping_collection:
                writer.writerow((pair.src, pair.dst))
        return {"FINISHED"}

class VERTEX_GROUP_RENAMER_MT_MappingCollection_Special(bpy.types.Menu):
    bl_idname = "VERTEX_GROUP_RENAMER_MT_mapping_collection_special"
    bl_label = "mapping collection's menu"
    def draw(self, context):
        layout = self.layout
        layout.operator(VERTEX_GROUP_RENAMER_OT_MappingCollection_Clear.bl_idname, text="Clear", icon="TRASH")
        layout.separator()
        layout.operator(VERTEX_GROUP_RENAMER_OT_MappingCollection_Import.bl_idname, text="import from csv")
        layout.operator(VERTEX_GROUP_RENAMER_OT_MappingCollection_Export.bl_idname, text="export to csv")

class VERTEX_GROUP_RENAMER_PT_ToolShelf(bpy.types.Panel):
    bl_idname = "VERTEX_GROUP_RENAMER_PT_tool_shelf"
    bl_label = "VertexGroup Renamer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Renamer'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.VertexGroupRenamerProperty
        layout.label(text="Armature pair")
        layout.prop(props, "armature_source")
        layout.prop(props, "armature_target")
        layout.prop(props, "bone_max_distance")
        layout.operator(VERTEX_GROUP_RENAMER_OT_GetMappingFromArmaturePair.bl_idname, text="Get Mapping from Armature")
        layout.separator()

        layout.label(text="Mapping Pair")
        row = layout.row()
        row.template_list(VERTEX_GROUP_RENAMER_UL_MappingPair.__name__, "", props, "mapping_collection", props, "mapping_active_index")
        side = row.column()
        col = side.column(align=True)
        col.operator(VERTEX_GROUP_RENAMER_OT_MappingCollection_Add.bl_idname, text="", icon="ADD")
        col.operator(VERTEX_GROUP_RENAMER_OT_MappingCollection_Remove.bl_idname, text="", icon="REMOVE")
        side.separator()
        side.menu(VERTEX_GROUP_RENAMER_MT_MappingCollection_Special.bl_idname, text="", icon="DOWNARROW_HLT")
        
        layout.separator()
        layout.operator(VERTEX_GROUP_RENAMER_OT_Rename.bl_idname, text="Rename VertexGroup")

class VERTEX_GROUP_RENAMER_OT_GetMappingFromArmaturePair(bpy.types.Operator):
    bl_idname = "vertex_group_renamer.get_mapping_from_armature_pair"
    bl_label = "get mapping from armature pair"
    bl_description = "get mapping from armature pair."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        props = scene.VertexGroupRenamerProperty
        armature_src = props.armature_source
        armature_dst = props.armature_target
        bone_max_distance = props.bone_max_distance
        mapping_collection = props.mapping_collection

        if (armature_src is None) or (armature_dst is None):
            return {"CANCELLED"}
        
        matrix_world_src = armature_src.matrix_world
        matrix_world_dst = armature_dst.matrix_world

        # マッピング情報を取得
        bone_mapping = {}

        for bone_src in armature_src.data.bones:
            mapped_bone = None
            # 名前を元にマッピング
            for bone_trg in armature_dst.data.bones:
                if bone_src.name == bone_trg.name:
                    mapped_bone = bone_trg
                    break
            
            if mapped_bone is not None:
                bone_mapping[bone_src.name] = mapped_bone.name
                continue
       
            # 同じ名前のボーンが無く、同じ階層のボーンがあれば、Headが一番近いボーンにマッピング
            bone_src_depth = len(bone_src.parent_recursive)
            minimum_distance = None
            for bone_trg in armature_dst.data.bones:
                bone_trg_depth = len(bone_trg.parent_recursive)
                if bone_src_depth == bone_trg_depth:
                    src_pos = matrix_world_src @ bone_src.head_local
                    dst_pos = matrix_world_dst @ bone_trg.head_local
                    distance = (src_pos - dst_pos).length
                    if (distance <= bone_max_distance) and ((minimum_distance is None) or (minimum_distance > distance)):
                        minimum_distance = distance
                        mapped_bone = bone_trg
            
            # マッピング先が無ければ、空文字でマッピング
            if mapped_bone is not None:
                bone_mapping[bone_src.name] = mapped_bone.name
            else:
                bone_mapping[bone_src.name] = ""

        # mappingをコレクションに変換
        mapping_collection.clear()
        for src, dst in bone_mapping.items():
            pair = mapping_collection.add()
            pair.src = src
            pair.dst = dst
        return {"FINISHED"}


class VERTEX_GROUP_RENAMER_OT_Rename(bpy.types.Operator):
    bl_idname = "vertex_group_renamer.rename"
    bl_label = "Rename VertexGroup"
    bl_description = "Rename VertexGroup with mapping."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        mapping = {}
        mapping_collection = context.scene.VertexGroupRenamerProperty.mapping_collection
        for pair in mapping_collection:
            mapping[pair.src] = pair.dst

        # 選択したMeshのVertex Group名を変更
        for obj in bpy.context.selected_objects:
            if obj.type == 'MESH':
                for vg in obj.vertex_groups:
                    if vg.name in mapping:
                        mapped_name = mapping[vg.name]
                        if mapped_name != "":
                            vg.name = mapped_name

        return {'FINISHED'}

classes = [
    MappingPairProperty,
    VertexGroupRenamerProperties,
    VERTEX_GROUP_RENAMER_OT_MappingCollection_Add,
    VERTEX_GROUP_RENAMER_OT_MappingCollection_Remove,
    VERTEX_GROUP_RENAMER_OT_MappingCollection_Clear,
    VERTEX_GROUP_RENAMER_OT_MappingCollection_Import,
    VERTEX_GROUP_RENAMER_OT_MappingCollection_Export,
    VERTEX_GROUP_RENAMER_MT_MappingCollection_Special,
    VERTEX_GROUP_RENAMER_UL_MappingPair,
    VERTEX_GROUP_RENAMER_OT_Rename,
    VERTEX_GROUP_RENAMER_OT_GetMappingFromArmaturePair,
    VERTEX_GROUP_RENAMER_PT_ToolShelf,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.VertexGroupRenamerProperty = bpy.props.PointerProperty(type=VertexGroupRenamerProperties)

def unregister():
    del bpy.types.Scene.VertexGroupRenamerProperty
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
