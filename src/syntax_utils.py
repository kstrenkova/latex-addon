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
        self.context = context
        self.text_scale = custom_prop.text_scale
        self.base_font = custom_prop.font_path
        self.base_coll = ""
        self.current_coll = ""


# class for parameters
class Parameters:
    def __init__(self, scale, height, width, line):
        self.scale = scale
        self.height = height
        self.width = width
        self.line = line

    def create_copy(self):
        copy = Parameters(self.scale, self.height, self.width, self.line)
        return copy


# Function returns font info
def change_font(mode):
    return FONT_CACHE.get(mode)


# Function preloads fonts used by the addon
def preload_fonts():
    font_mode = {
        'math': ('Kelvinch Regular', 'Kelvinch-Roman.otf'),
        'mathcal': ('Latin Modern Math Regular', 'latinmodern-math.otf'),
    }

    src_dir = os.path.dirname(os.path.dirname(__file__))
    fonts_dir = os.path.join(src_dir, "data", "fonts")

    for mode, (font_name, filename) in font_mode.items():
        if font_name in bpy.data.fonts:
            font = bpy.data.fonts[font_name]
        else:
            font_file = os.path.join(fonts_dir, filename)
            font = bpy.data.fonts.load(font_file)

        font_size = get_font_scale(font)
        FONT_CACHE[mode] = {'font': font, 'size': font_size}

    print("FONT CACHE:", FONT_CACHE.items())


def get_font_scale(font):
    bpy.ops.object.text_add()
    h_obj = bpy.context.active_object

    h_obj.data.font = font
    h_obj.data.body = 'H'
    bpy.context.view_layer.update()

    # base blender font size is 0.6820
    size = 0.6820 / h_obj.dimensions.y

    print(f"The height of the text object is: {h_obj.dimensions.y:.4f} Blender Units")

    bpy.ops.object.delete(use_global=False)

    return round(size, 4)
