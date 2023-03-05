bl_info = {
    "name": "VertexGroup Renamer",
    "author": "takec",
    "version": (1, 0),
    "blender": (3, 4, 0),
    "location": "View3D > Tool Shelf > Renamer > VertexGroup Renamer",
    "description": "Renames vertex groups based on bone mappings",
    "category": "Object"
}

import bpy

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

class VertexGroupRenamer_UL_MappingPair(bpy.types.UIList):
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

class MappingCollection_OT_Add(bpy.types.Operator):
    bl_idname = "mapping_collection.add"
    bl_label = "add mapping_pair to collection"
    def execute(self, context):
        context.scene.VertexGroupRenamerProperty.mapping_collection.add()
        return {"FINISHED"}

class MappingCollection_OT_Remove(bpy.types.Operator):
    bl_idname = "mapping_collection.remove"
    bl_label = "remove mapping_pair from collection"
    def execute(self, context):
        props = context.scene.VertexGroupRenamerProperty
        mapping_collection = props.mapping_collection
        active_index = props.mapping_active_index
        mapping_collection.remove(active_index)
        active_index = min(active_index, len(mapping_collection)-1)
        return {"FINISHED"}

class MappingCollection_OT_Clear(bpy.types.Operator):
    bl_idname = "mapping_collection.clear"
    bl_label = "clear mapping collection"
    def execute(self, context):
        props = context.scene.VertexGroupRenamerProperty
        mapping_collection = props.mapping_collection
        mapping_collection.clear()
        return {"FINISHED"}

class VertexGroupRenamePanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_vertex_group_rename_panel"
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
        layout.operator(VertexGroupRenamer_OT_GetMappingFromArmaturePair.bl_idname, text="Get Mapping from Armature")
        layout.separator()

        layout.label(text="Mapping Pair")
        row = layout.row()
        row.template_list("VertexGroupRenamer_UL_MappingPair", "", props, "mapping_collection", props, "mapping_active_index")
        col = row.column()
        col.operator(MappingCollection_OT_Add.bl_idname, text="", icon="ADD")
        col.operator(MappingCollection_OT_Remove.bl_idname, text="", icon="REMOVE")
        col.operator(MappingCollection_OT_Clear.bl_idname, text="", icon="TRASH")
        
        layout.separator()
        layout.operator(VertexGroupRenamer_OT_Rename.bl_idname, text="Rename VertexGroup")

class VertexGroupRenamer_OT_GetMappingFromArmaturePair(bpy.types.Operator):
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
        print(matrix_world_src)
        print(matrix_world_dst)

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
                    print(bone_src.name, bone_trg.name, src_pos, dst_pos, distance)
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


class VertexGroupRenamer_OT_Rename(bpy.types.Operator):
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
    MappingCollection_OT_Add,
    MappingCollection_OT_Remove,
    MappingCollection_OT_Clear,
    VertexGroupRenamerProperties,
    VertexGroupRenamer_UL_MappingPair,
    VertexGroupRenamer_OT_Rename,
    VertexGroupRenamer_OT_GetMappingFromArmaturePair,
    VertexGroupRenamePanel,
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
