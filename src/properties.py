# ---------------------------------------------------------------------------
# File name   : properties.py
# Created By  : Katarina Strenkova
# ---------------------------------------------------------------------------

import bpy


# callback gets all of the loaded fonts
def get_loaded_fonts(self, context):
    fonts = [('Bfont Regular', 'Bfont Regular', '<builtin>')]

    # add all loaded fonts
    for font in bpy.data.fonts:
        if font.name != 'Bfont Regular':
            fonts.append((font.name, font.name, font.filepath))
    return fonts


# custom properties
# TODO [feature] add text alignment, math font
class LATEX_PG_Properties(bpy.types.PropertyGroup):
    latex_text: bpy.props.StringProperty(
        name="Text",
        description="Input text in LaTeX formatting",
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

    show_transform: bpy.props.BoolProperty(
        name="",
        description="Transform output text",
        default=False
    ) # type: ignore

    text_scale: bpy.props.FloatProperty(
        name="Scale:",
        description="Scale of the output text",
        default=1.0,
        min=0.01
    ) # type: ignore

    text_thickness: bpy.props.FloatProperty(
        name="Thickness:",
        description="Thickness of the output text",
        default=0.1,
        min=0.0
    ) # type: ignore

    line_height: bpy.props.FloatProperty(
        name="Line height:",
        description="Vertical spacing between lines",
        default=1.0,
        soft_min=0.8,
        soft_max=3.0,
        step=5,
    ) # type: ignore

    word_space: bpy.props.FloatProperty(
        name="Word spacing:",
        description="Horizontal spacing between words",
        default=0.3,
        soft_min=0.0,
        soft_max=2.0,
        step=5
    ) # type: ignore

    one_object: bpy.props.BoolProperty(
        name="Generate as one object",
        default=False
    ) # type: ignore
