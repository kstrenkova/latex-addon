# ---------------------------------------------------------------------------
# File name   : ui.py
# Created By  : Katarina Strenkova
# ---------------------------------------------------------------------------

import bpy
import os

from bpy.props import (StringProperty,
                       BoolProperty,
                       EnumProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       PointerProperty,
                       )

from mathutils import Vector  # vertices

# functions from analyser
from .lexical_analyser import LexicalAnalyser
from .syntax_analyser import SyntaxAnalyser


def get_loaded_fonts(self, context):
    items = []
    for font in bpy.data.fonts:
        items.append((font.name, font.name, font.filepath))
    return items


# custom properties
class Custom_PT(bpy.types.PropertyGroup):

    latex_text: StringProperty(
        name="Latex text",
        default=""
    ) # type: ignore

    show_font: BoolProperty(
        name="",
        description="Choose custom fonts for your text",
        default=False
    ) # type: ignore

    font_path: StringProperty(
        name = "",
        description="Specify a path to a font you want to get loaded",
        default="",
        maxlen=1024,
        subtype='FILE_PATH'
    ) # type: ignore

    base_font: EnumProperty(
        name = "Base",
        description="Choose a font for basic text",
        items=get_loaded_fonts
    ) # type: ignore

    bold_font: EnumProperty(
        name = "Bold",
        description="Choose a font for bold text",
        items=get_loaded_fonts
    ) # type: ignore

    italic_font: EnumProperty(
        name = "Italic",
        description="Choose a font for italic text",
        items=get_loaded_fonts
    ) # type: ignore

    text_scale: FloatProperty(
        name="Scale:",
        default=1.0,
        min=0.01
    ) # type: ignore

    text_thickness: FloatProperty(
        name="Thickness:",
        default=0.0,
        min=0.0
    ) # type: ignore

    text_location: FloatVectorProperty(
        name="Location",
        subtype='XYZ'
    ) # type: ignore

    text_rotation: FloatVectorProperty(
        name="Rotation",
        subtype='EULER'
    ) # type: ignore

    one_object: BoolProperty(
        name="Generate as one object",
        default=False
    ) # type: ignore

# main addon panel
class OBJECT_PT_ME(bpy.types.Panel):
    bl_label = "Latex Text"
    bl_idname = "OBJECT_PT_ME"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Latex Text'

    # drawing main panel
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        cus_pt = scene.custom_prop

        layout.prop(cus_pt, "latex_text")

        row = layout.row()
        row.label(text="Custom Fonts")
        row.prop(cus_pt, "show_font", emboss=False,
                 icon="TRIA_DOWN" if cus_pt.show_font else "TRIA_RIGHT")

        # collapse font area
        if cus_pt.show_font:
            box = layout.box()
            box.prop(cus_pt, "font_path")
            box.operator("wm.loadfont")

            box2 = layout.box()
            box2.prop(cus_pt, "base_font")
            box2.prop(cus_pt, "bold_font")
            box2.prop(cus_pt, "italic_font")

        layout.prop(cus_pt, "text_scale")
        layout.prop(cus_pt, "text_thickness")

        row = layout.row(align=True)

        col = row.column()
        col.prop(cus_pt,'text_location')

        col2 = row.column()
        col2.prop(cus_pt,'text_rotation')

        layout.prop(cus_pt, "one_object")

        row2 = layout.row(align=True)
        row2.operator("wm.addtextop")


# load font
# TODO when the font is already loaded, don't load
class WM_OT_LoadFont(bpy.types.Operator):
    bl_label = "Load font"
    bl_idname = "wm.loadfont"

    def execute(self, context):
        scene = context.scene
        props = scene.custom_prop

        # get the absolute path of the new font
        font_path = bpy.path.abspath(props.font_path)
        font_path_norm = os.path.normpath(font_path)

        # compare font paths until you get an equal
        for font in bpy.data.fonts:
            if os.path.normpath(bpy.path.abspath(font.filepath)) == font_path_norm:
                self.report({'INFO'}, f"Font already loaded: {font.name}")
                return {'FINISHED'}

        # load new font
        font = bpy.data.fonts.load(font_path)
        self.report({'INFO'}, f"New font loaded: {font.name}")
        return {'FINISHED'}


# add text
class WM_OT_AddText(bpy.types.Operator):
    bl_label = "Add Text"
    bl_idname = "wm.addtextop"

    def execute(self, context):
        scene = context.scene
        cus_pt = scene.custom_prop

        # create lexical analyser and main syntax analyser
        lex = LexicalAnalyser(cus_pt.latex_text, 0)
        syntax = SyntaxAnalyser(lex, context, cus_pt)

        # parse latex text
        if not syntax.parse():
            warn_msg = 'Latex text was not fully generated. Check system console for more info on this matter.'
            self.report({'WARNING'}, warn_msg)

        # all objects in latex text
        all_obj = context.selected_objects

        if len(all_obj) > 1 and cus_pt.one_object:
            generate_one_object(context, cus_pt)
        else:
            # add empty object
            bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0,0,0))
            empty_obj = context.active_object

            for obj in all_obj:
                # set thickness
                if obj.type == 'FONT':
                    # for text change extrude parameter
                    obj.data.extrude = cus_pt.text_thickness / 2.0
                else:
                    # for other objects apply solidify modifier
                    solidify_mod = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
                    solidify_mod.thickness = cus_pt.text_thickness
                    solidify_mod.offset = 0.0

                # set empty object as parent
                obj.parent = empty_obj

            empty_obj.location = cus_pt.text_location                     # move empty object
            empty_obj.rotation_euler = cus_pt.text_rotation               # rotate empty object
            bpy.ops.object.transform_apply(location=True, rotation=True)  # apply transformation
            bpy.ops.object.delete()                                       # delete empty object

        return {'FINISHED'}


# enumeration of all my classes
all_classes = [
    Custom_PT,
    OBJECT_PT_ME,
    WM_OT_LoadFont,
    WM_OT_AddText
]


# function generates the final latex text as one object
def generate_one_object(context, cus_pt):
    all_obj = context.selected_objects
    all_converted_obj = []

    for obj in all_obj:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj

        # convert text objects to meshes
        if obj.type == 'FONT':
            bpy.ops.object.convert(target='MESH')

        all_converted_obj.append(context.active_object)

    # select all latex text objects
    for obj in all_converted_obj:
        obj.select_set(True)

    # join all objects into one
    context.view_layer.objects.active = all_converted_obj[0]
    bpy.ops.object.join()

    final_obj = context.active_object
    final_obj.name = "Latex Text"
    final_obj.location = cus_pt.text_location                     # move object
    final_obj.rotation_euler = cus_pt.text_rotation               # rotate object
    bpy.ops.object.transform_apply(location=True, rotation=True)  # apply transformation

    # apply solidify modifier
    solidify_mod = final_obj.modifiers.new(name="Solidify", type='SOLIDIFY')
    solidify_mod.thickness = cus_pt.text_thickness
    solidify_mod.offset = 0.0

    # delete base latex collection
    for collection in list(final_obj.users_collection):
        if "LatexCollection" in collection.name:
            context.scene.collection.objects.link(final_obj)
            collection.objects.unlink(final_obj)
            bpy.data.collections.remove(collection)


def register():
    for cls in all_classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.custom_prop = PointerProperty(type=Custom_PT)


def unregister():
    for cls in all_classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.custom_prop
