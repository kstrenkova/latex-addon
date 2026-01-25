# ---------------------------------------------------------------------------
# File name   : ui.py
# Created By  : Katarina Strenkova
# ---------------------------------------------------------------------------

import bpy
import os

# functions from analyser
from .lexical_analyser import LexicalAnalyser
from .syntax_analyser import SyntaxAnalyser

TMP_TEXT_EDIT = "tmp_latex_text_edit"

# TODO [bug] fix messy letters in generate_1_object when thickness is not zero
# TODO [bug] fix different final position for 1 object vs multiple objects

# function gets all of the loaded fonts
def get_loaded_fonts(self, context):
    fonts = [('Bfont Regular', 'Bfont Regular', '<builtin>')]
    for font in bpy.data.fonts:
        if font.name != 'Bfont Regular':
            fonts.append((font.name, font.name, font.filepath))
    return fonts


# custom properties
class LATEX_PG_Properties(bpy.types.PropertyGroup):
    latex_text: bpy.props.StringProperty(
        name="Text",
        description="Input text in Latex formatting",
        default=""
    ) # type: ignore

    show_font: bpy.props.BoolProperty(
        name="",
        description="Choose custom fonts for your text",
        default=False
    ) # type: ignore

    font_path: bpy.props.StringProperty(
        name = "",
        description="Specify a path to a font you want to get loaded",
        default="",
        maxlen=1024,
        subtype='FILE_PATH'
    ) # type: ignore

    base_font: bpy.props.EnumProperty(
        name = "Base",
        description="Choose a font for basic text",
        items=get_loaded_fonts
    ) # type: ignore

    bold_font: bpy.props.EnumProperty(
        name = "Bold",
        description="Choose a font for bold text",
        items=get_loaded_fonts
    ) # type: ignore

    italic_font: bpy.props.EnumProperty(
        name = "Italic",
        description="Choose a font for italic text",
        items=get_loaded_fonts
    ) # type: ignore

    text_scale: bpy.props.FloatProperty(
        name="Scale:",
        default=1.0,
        min=0.01
    ) # type: ignore

    text_thickness: bpy.props.FloatProperty(
        name="Thickness:",
        default=0.0,
        min=0.0
    ) # type: ignore

    text_location: bpy.props.FloatVectorProperty(
        name="Location",
        subtype='XYZ'
    ) # type: ignore

    text_rotation: bpy.props.FloatVectorProperty(
        name="Rotation",
        subtype='EULER'
    ) # type: ignore

    one_object: bpy.props.BoolProperty(
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
        props = context.scene.custom_prop

        row = layout.row(align=True)
        row.prop(props, "latex_text")
        row.operator("text.edit_text", text="", icon='TEXT')

        row = layout.row()
        row.label(text="Custom Fonts")
        row.prop(props, "show_font", emboss=False,
                icon="TRIA_DOWN" if props.show_font else "TRIA_RIGHT")

        # collapse font area
        if props.show_font:
            box = layout.box()
            box.prop(props, "font_path")
            box.operator("wm.load_font")

            box2 = layout.box()
            box2.prop(props, "base_font")
            box2.prop(props, "bold_font")
            box2.prop(props, "italic_font")

        layout.prop(props, "text_scale")
        layout.prop(props, "text_thickness")

        row = layout.row(align=True)

        col = row.column()
        col.prop(props,'text_location')

        col2 = row.column()
        col2.prop(props,'text_rotation')

        layout.prop(props, "one_object")

        row2 = layout.row(align=True)
        row2.operator("wm.add_text")


# text editor helper panel
class TEXT_PT_LatexEditor(bpy.types.Panel):
    bl_label = "Save Latex Text"
    bl_idname = "TEXT_PT_LatexEditor"
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Text'

    @classmethod
    def poll(cls, context):
        # show panel only when editing latex text
        return TMP_TEXT_EDIT in bpy.data.texts

    def draw(self, context):
        layout = self.layout
        layout.operator("text.save_and_return", icon='FILE_TICK')


# edit text
class TEXT_OT_EditText(bpy.types.Operator):
    """Open text editor for Latex text"""
    bl_idname = "text.edit_text"
    bl_label = "Edit Text"

    def execute(self, context):
        # create a new text block
        if TMP_TEXT_EDIT in bpy.data.texts:
            bpy.data.texts.remove(bpy.data.texts[TMP_TEXT_EDIT])
        text = bpy.data.texts.new(name=TMP_TEXT_EDIT)

        # load text from the text field
        props = context.scene.custom_prop
        text.write(props.latex_text)

        # switch to a text editor
        context.area.type = 'TEXT_EDITOR'
        context.area.spaces.active.text = text

        return {'FINISHED'}


# save and return to the 3D view
class TEXT_OT_SaveAndReturn(bpy.types.Operator):
    """Save edited Latex text and return to the 3D view"""
    bl_idname = "text.save_and_return"
    bl_label = "Save & Return"

    def execute(self, context):
        # get the text block
        text = bpy.data.texts.get(TMP_TEXT_EDIT)
        if text:
            props = context.scene.custom_prop
            props.latex_text = text.as_string()  # save the text
            bpy.data.texts.remove(text)          # remove text block

        # return to the 3D view
        context.area.type = 'VIEW_3D'

        self.report({'INFO'}, "Latex text has been updated")
        return {'FINISHED'}


# load font
class WM_OT_LoadFont(bpy.types.Operator):
    """Load a font"""
    bl_label = "Load font"
    bl_idname = "wm.load_font"

    def execute(self, context):
        props = context.scene.custom_prop

        # get the absolute path of the new font
        font_path = bpy.path.abspath(props.font_path)
        font_path_norm = os.path.normpath(font_path)

        # clean the user input to signal change
        props.font_path = ""

        # compare font paths until you get a match
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
    """Add text in Latex formatting to the 3D view"""
    bl_label = "Add Text"
    bl_idname = "wm.add_text"

    def execute(self, context):
        props = context.scene.custom_prop

        # create lexical analyser and main syntax analyser
        lex = LexicalAnalyser(props.latex_text, 0, "text")
        syntax = SyntaxAnalyser(lex, context, props)

        # parse latex text
        if not syntax.parse():
            warn_msg = 'Latex text was not fully generated: Check system console for more information'
            self.report({'WARNING'}, warn_msg)
            return {'CANCELLED'}

        # all objects in latex text
        all_obj = context.selected_objects

        if len(all_obj) >= 1 and props.one_object:
            generate_one_object(context, props)
        else:
            # add empty object
            bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0,0,0))
            empty_obj = context.active_object

            for obj in all_obj:
                # set thickness
                if obj.type == 'FONT':
                    # for text change extrude parameter
                    obj.data.extrude = props.text_thickness / 2.0
                else:
                    # for other objects apply solidify modifier
                    solidify_mod = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
                    solidify_mod.thickness = props.text_thickness
                    solidify_mod.offset = 0.0

                # set empty object as parent
                obj.parent = empty_obj

            empty_obj.location = props.text_location                      # move empty object
            empty_obj.rotation_euler = props.text_rotation                # rotate empty object
            bpy.ops.object.transform_apply(location=True, rotation=True)  # apply transformation
            bpy.ops.object.delete()                                       # delete empty object

        self.report({'INFO'}, "Latex text was generated successfully")
        return {'FINISHED'}


# function generates the final latex text as one object
def generate_one_object(context, props):
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
    final_obj.location = props.text_location        # move object
    final_obj.rotation_euler = props.text_rotation  # rotate object

    # apply transformations
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # apply solidify modifier
    solidify_mod = final_obj.modifiers.new(name="Solidify", type='SOLIDIFY')
    solidify_mod.thickness = props.text_thickness
    solidify_mod.offset = 0.0

    # delete base latex collection
    for collection in list(final_obj.users_collection):
        if "LatexCollection" in collection.name:
            context.scene.collection.objects.link(final_obj)
            collection.objects.unlink(final_obj)
            bpy.data.collections.remove(collection)


# enumeration of all my classes
all_classes = [
    LATEX_PG_Properties,
    OBJECT_PT_ME,
    TEXT_PT_LatexEditor,
    TEXT_OT_EditText,
    TEXT_OT_SaveAndReturn,
    WM_OT_LoadFont,
    WM_OT_AddText
]


def register():
    for cls in all_classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.custom_prop = bpy.props.PointerProperty(type=LATEX_PG_Properties)


def unregister():
    for cls in all_classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.custom_prop
