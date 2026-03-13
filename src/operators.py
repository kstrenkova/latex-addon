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
    bl_label = "Load font"
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

        # except Exception as e:
        #     self.report({'ERROR'}, f"Python Error: {e}")
        #     print(f"Developer Traceback: {e}")
        #     return {'CANCELLED'}

        finally:
            # set cursor icon back to default
            bpy.context.window.cursor_modal_restore()

        # all objects in LaTeX text
        all_obj = context.selected_objects

        if len(all_obj) >= 1 and props.one_object:
            generate_one_object(context, props)
        else:
            cursor_pos = bpy.context.scene.cursor.location.copy()

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

                # move to cursor location
                obj.location += cursor_pos

        self.report({'INFO'}, "LaTeX text was generated successfully")
        return {'FINISHED'}


# function generates the final LaTeX text as one object
# TODO [bug] fix messy letters when thickness is not zero
def generate_one_object(context, props):
    all_obj = context.selected_objects
    all_converted_obj = []

    # deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    for obj in all_obj:
        obj.select_set(True)
        context.view_layer.objects.active = obj

        # convert text objects to meshes
        if obj.type == 'FONT':
            bpy.ops.object.convert(target='MESH')

        # save and deselect object
        converted = context.active_object
        all_converted_obj.append(converted)
        converted.select_set(False)

    # select all LaTeX text objects
    for obj in all_converted_obj:
        obj.select_set(True)

    # join all objects into one
    context.view_layer.objects.active = all_converted_obj[0]
    bpy.ops.object.join()

    # set object location to 3D cursor location
    final_obj = context.active_object
    final_obj.name = "LaTeX Text"
    final_obj.location += bpy.context.scene.cursor.location.copy()

    # apply solidify modifier
    solidify_mod = final_obj.modifiers.new(name="Solidify", type='SOLIDIFY')
    solidify_mod.thickness = props.text_thickness
    solidify_mod.offset = 0.0

    # delete base LaTeX collection
    for collection in list(final_obj.users_collection):
        if "LaTeXCollection" in collection.name:
            context.scene.collection.objects.link(final_obj)
            collection.objects.unlink(final_obj)
            bpy.data.collections.remove(collection)
