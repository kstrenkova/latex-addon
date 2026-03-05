# ---------------------------------------------------------------------------
# File name   : panels.py
# Created By  : Katarina Strenkova
# ---------------------------------------------------------------------------

import bpy

TMP_TEXT_EDIT = "tmp_latex_text_edit"


# main addon panel
class OBJECT_PT_ME(bpy.types.Panel):
    bl_label = "LaTeX Text"
    bl_idname = "OBJECT_PT_ME"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LaTeX Text'

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

        row = layout.row()
        row.label(text="Transform Text")
        row.prop(props, "show_transform", emboss=False,
                icon="TRIA_DOWN" if props.show_transform else "TRIA_RIGHT")

        # collapse transform area
        if props.show_transform:
            box = layout.box()
            box.prop(props, "text_scale")
            box.prop(props, "text_thickness")
            box.prop(props, "line_height")
            box.prop(props, "word_space")
            box.operator("wm.reset_param", icon='FILE_REFRESH')

        layout.prop(props, "one_object")

        row2 = layout.row(align=True)
        row2.operator("wm.add_text")


# text editor helper panel
class TEXT_PT_LaTeXEditor(bpy.types.Panel):
    bl_label = "Save LaTeX Text"
    bl_idname = "TEXT_PT_LaTeXEditor"
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Text'

    @classmethod
    def poll(cls, context):
        # show panel only when editing LaTeX text
        return TMP_TEXT_EDIT in bpy.data.texts

    def draw(self, context):
        layout = self.layout
        layout.operator("text.save_and_return", icon='FILE_TICK')
