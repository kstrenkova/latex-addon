# ---------------------------------------------------------------------------
# File name   : syntax_utils.py
# Created By  : Katarina Strenkova
# ---------------------------------------------------------------------------

import bpy
import os.path

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


# TODO or we could load all fonts first and then just use them :thinking:
# -> depends on how many there are, but should definitely think about using cache at least
# Change font to one that is included in the addon
def change_font(mode):
    # TODO change mode names
    font_mode = {
        'math': 'Kelvinch-Roman.ot',
        'mathcal': 'latinmodern-math.otf',
    }

    src_dir = os.path.dirname(os.path.dirname(__file__))
    font_file = os.path.join(src_dir, "data", "fonts", font_mode.get(mode))
    font = bpy.data.fonts.load(font_file)
    return font


# TODO check out fonttools, but the concern is if it's installed
def scale_font():
    print("This function will scale font!")
