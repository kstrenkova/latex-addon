# ---------------------------------------------------------------------------
# File name   : syntax_utils.py
# Created By  : Katarina Strenkova
# ---------------------------------------------------------------------------


# class for defaults
class Defaults:
    def __init__(self, context, custom_prop):
        self.context = context
        self.text_scale = custom_prop.text_scale
        self.font_path = custom_prop.font_path
        self.font = []  # default_font, unicode_font
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