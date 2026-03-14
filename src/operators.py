# ---------------------------------------------------------------------------
# File name   : operators.py
# Created By  : Katarina Strenkova
# ---------------------------------------------------------------------------

import bpy
import os

# functions from analyser
from .lexical_analyser import LexicalAnalyser
from .syntax_analyser import SyntaxAnalyser

TMP_TEXT_EDIT = "tmp_latex_text_edit"


# edit text
class TEXT_OT_EditText(bpy.types.Operator):
    """Open text editor for LaTeX text"""
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
    """Save edited LaTeX text and return to the 3D view"""
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

        self.report({'INFO'}, "LaTeX text has been updated")
        return {'FINISHED'}


# load font
class WM_OT_LoadFont(bpy.types.Operator):
    """Load a font file for LaTeX text generation"""
    bl_label = "Load Font"
    bl_idname = "wm.load_font"

    def execute(self, context):
        props = context.scene.custom_prop
        base_font = props.base_font
        bold_font = props.bold_font
        italic_font = props.italic_font

        # check if user specified a font path
        if not props.font_path or not props.font_path.strip():
            self.report({'ERROR'}, "Please specify font path")
            return {'CANCELLED'}

        # get the absolute path of the new font
        font_path = bpy.path.abspath(props.font_path)
        font_path_norm = os.path.normpath(font_path)

        # clean the user input to signal change
        props.font_path = ""

        # check if file exists
        if not os.path.exists(font_path_norm):
            self.report({'ERROR'}, f"Font file not found: {font_path_norm}")
            return {'CANCELLED'}

        # compare font paths until you get a match
        for font in bpy.data.fonts:
            if os.path.normpath(bpy.path.abspath(font.filepath)) == font_path_norm:
                self.report({'INFO'}, f"Font already loaded: {font.name}")
                return {'FINISHED'}

        try:
            # load new font
            font = bpy.data.fonts.load(font_path_norm)
            self.report({'INFO'}, f"New font loaded: {font.name}")

            # restore previous font selections
            props.base_font = base_font
            props.bold_font = bold_font
            props.italic_font = italic_font

            return {'FINISHED'}
        except RuntimeError as e:
            self.report({'ERROR'}, f"Failed to load font: {str(e)}")
            return {'CANCELLED'}


# reset parameters
class WM_OT_ResetParameters(bpy.types.Operator):
    """Reset transform parameters to default values"""
    bl_label = "Reset Parameters"
    bl_idname = "wm.reset_param"

    def execute(self, context):
        props = context.scene.custom_prop

        # set transform parameters to default values
        props.text_scale = 1.0
        props.text_thickness = 0.1
        props.line_height = 1.0
        props.word_space = 0.3
        props.block_space = 1.6

        self.report({'INFO'}, "Transform parameters reset")
        return {'FINISHED'}


# add text
class WM_OT_AddText(bpy.types.Operator):
    """Add text in LaTeX formatting to the 3D view"""
    bl_label = "Add Text"
    bl_idname = "wm.add_text"

    def execute(self, context):
        props = context.scene.custom_prop

        # create lexical analyser and main syntax analyser
        lex = LexicalAnalyser(props.latex_text, 0)
        syntax = SyntaxAnalyser(lex, context, props)

        # set cursor icon to loading
        bpy.context.window.cursor_modal_set('WAIT')

        try:
            # parse LaTeX text
            if not syntax.parse():
                warn_msg = 'LaTeX text was not fully generated: Check system console for more information'
                self.report({'WARNING'}, warn_msg)
                return {'CANCELLED'}

        except Exception as e:
            print(f"Developer Traceback: {e}")
            self.report({'ERROR'}, f"Python Error: {e}")
            return {'CANCELLED'}

        finally:
            # set cursor icon back to default
            bpy.context.window.cursor_modal_restore()

        # all objects in LaTeX text
        all_obj = context.selected_objects
        cursor_pos = bpy.context.scene.cursor.location.copy()

        if len(all_obj) >= 1 and props.one_object:
            generate_one_object(context, props, all_obj)
        else:
            for obj in all_obj:
                # set thickness and location
                apply_thickness(obj, props.text_thickness)
                obj.location += cursor_pos

        self.report({'INFO'}, "LaTeX text was generated successfully")
        return {'FINISHED'}


# function applies thickness based on object type
def apply_thickness(obj, thickness):
    if obj.type == 'FONT':
        # for text change extrude parameter
        obj.data.extrude = thickness / 2.0
    else:
        # for other objects add solidify modifier
        mod = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
        mod.thickness = thickness
        mod.offset = 0.0


# function generates the final LaTeX text as one object
def generate_one_object(context, props, all_obj):
    # deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    for obj in all_obj:
        # set thickeness
        apply_thickness(obj, props.text_thickness)

        obj.select_set(True)
        context.view_layer.objects.active = obj

        # convert text object to mesh
        if obj.type == 'FONT':
            bpy.ops.object.convert(target='MESH')
        else:
            bpy.ops.object.modifier_apply(modifier="Solidify")

    # join all objects into one
    context.view_layer.objects.active = context.selected_objects[0]
    bpy.ops.object.join()

    # set object location to 3D cursor location
    final_obj = context.active_object
    final_obj.name = "LaTeX Text"
    final_obj.location += bpy.context.scene.cursor.location.copy()

    # delete base LaTeX collection
    for collection in list(final_obj.users_collection):
        if "LaTeXCollection" in collection.name:
            context.scene.collection.objects.link(final_obj)
            collection.objects.unlink(final_obj)
            bpy.data.collections.remove(collection)
