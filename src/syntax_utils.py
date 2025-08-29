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

# TODO add working with fonts
# Change font to one that is included in the addon
def change_font(mode):
    # TODO cleanup, change mode names
    if mode == 'math':
        name = "Kelvinch-Roman.otf"
    elif mode == 'mathcal':
        name = "latinmodern-math.otf"

    src_dir = os.path.dirname(__file__)
    font_file = os.path.join(os.path.dirname(src_dir), "data", "fonts", name)
    font = bpy.data.fonts.load(font_file)
    return font
