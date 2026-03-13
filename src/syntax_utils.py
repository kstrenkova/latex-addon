# ---------------------------------------------------------------------------
# File name   : syntax_utils.py
# Created By  : Katarina Strenkova
# ---------------------------------------------------------------------------

import bpy
import os.path

FONT_CACHE = {}


# class for defaults
class Defaults:
    def __init__(self, context, custom_prop):
        self.base_coll = ""
        self.current_coll = ""
        self.context = context
        self.math_mode = 'inline'
        self.user_font = 'base'
        self.whitespace = False

        # parameters from custom properties
        self.block_space = custom_prop.block_space
        self.fonts = [
            custom_prop.base_font,
            custom_prop.bold_font,
            custom_prop.italic_font
        ]
        self.line_height = custom_prop.line_height
        self.text_scale = custom_prop.text_scale
        self.word_space = custom_prop.word_space


# class for lines
class Line:
    def __init__(self, height, table_objs=[], table_min_y=None):
        self.height = height
        self.line_objs = table_objs
        self.min_y = None

        # table specific parameters
        self.table_objs = table_objs
        self.table_min_y = table_min_y


# class for parameters
class Parameters:
    def __init__(self, scale, height, width):
        self.scale = scale
        self.height = height
        self.width = width
        self.line = Line(height)

    def create_copy(self):
        copy = Parameters(self.scale, self.height, self.width)
        return copy


# function returns font info
def change_font(mode):
    return FONT_CACHE.get(mode) if (mode in FONT_CACHE) else ''


# function preloads fonts used by the addon
def preload_fonts(context, user_fonts):
    font_mode = {
        'math':     ('STIX Two Math Regular',        'STIXTwoMath-Regular.ttf'),
        'teletype': ('Latin Modern Mono 10 Regular', 'latin-modern-mono.mmono10-regular.otf'),
        'verb':     ('Latin Modern Mono 10 Regular', 'latin-modern-mono.mmono10-regular.otf'),
    }

    src_dir = os.path.dirname(os.path.dirname(__file__))
    fonts_dir = os.path.join(src_dir, "fonts")

    for mode, (font_name, filename) in font_mode.items():
        if font_name in bpy.data.fonts:
            font = bpy.data.fonts[font_name]  # get preloaded font
        else:
            # load font
            font_file = os.path.join(fonts_dir, filename)
            font = bpy.data.fonts.load(font_file)

        font_size = get_font_scale(context, font)
        FONT_CACHE[mode] = {'font': font, 'size': font_size}

    user_mode = ['base', 'bold', 'italic']

    # load fonts specified by user
    for mode, font in zip(user_mode, user_fonts):
        user_font = bpy.data.fonts[font]
        font_size = get_font_scale(context, user_font)
        FONT_CACHE[mode] = {'font': user_font, 'size': font_size}


# function that gets font scale that is needed
# to make all fonts the same height
def get_font_scale(context, font):
    bpy.ops.object.text_add()
    h_obj = context.active_object

    h_obj.data.font = font
    h_obj.data.body = 'H'
    context.view_layer.update()

    # base blender font size is 0.6820 (for H)
    size = 0.6820 / h_obj.dimensions.y
    bpy.ops.object.delete(use_global=False)

    return round(size, 4)
