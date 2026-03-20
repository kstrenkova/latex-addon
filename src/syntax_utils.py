# ---------------------------------------------------------------------------
# File name   : syntax_utils.py
# Created By  : Katarina Strenkova
# ---------------------------------------------------------------------------

import bpy
import os.path

# ---------------
# COMMON CLASSES
# ---------------

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


class Line:
    def __init__(self, height, table_objs=[], table_min_y=None):
        self.height = height
        self.line_objs = table_objs
        self.min_y = None

        # table specific parameters
        self.table_objs = table_objs
        self.table_min_y = table_min_y


class Parameters:
    def __init__(self, scale, height, width):
        self.scale = scale
        self.height = height
        self.width = width
        self.line = Line(height)

    def create_copy(self):
        copy = Parameters(self.scale, self.height, self.width)
        return copy

# ------------------
# TEXT MODE CLASSES
# ------------------

class ItemizeState:
    def __init__(self, parent_coll, nest_array):
        self.parent_coll = parent_coll
        self.bullet_number = 0
        self.custom_bullet = False
        self.nest_array = nest_array


# single column alignment
class ColumnAlignment:
    def __init__(self, type):
        self.type = type
        self.width = -1
        self.unit = ''


class VLinePosition:
    def __init__(self, x_pos, ID):
        self.ID = ID  # it can be defined either by row or column number
        self.x_pos = x_pos
        self.y_pos = []


class TableAlignment:
    def __init__(self):
        self.columns = []
        self.vline = []
        self.vline_pos = []
        self.column_width = []
        self.row_y = []

    def add_vline_pos(self, x_pos, ID):
        self.vline_pos.append(VLinePosition(x_pos, ID))


class TableHorizontalLines:
    def __init__(self):
        self.hline_pos = []
        self.cline_pos = []
        self.cline_range = []
        self.cline_new = True

    def reset_cline(self):
        self.cline_new = True


class MultiRow():
    def __init__(self):
        self.span = 1
        self.width = -1
        self.unit = ''

    def reset_row_span(self):
        self.span = 1
        self.width = -1
        self.unit = ''


class MultiCol():
    def __init__(self):
        self.span = 1
        self.align = ColumnAlignment('c')
        self.before = 0
        self.after = 0

    def reset_col_span(self):
        self.span = 1
        self.align = ColumnAlignment('c')
        self.before = 0
        self.after = 0


class TableMultiCell:
    def __init__(self):
        self.row = MultiRow()
        self.col = MultiCol()
        self.vline_pos = []
        self.cell_span = {}

    # saves the multi-span state
    def save_cell_span(self, cell):
        self.cell_span[cell] = {
            'row_span': self.row.span,
            'row_width': self.row.width,
            'row_unit': self.row.unit,
            'col_span': self.col.span,
            'col_align': self.col.align,
            'vline_before': self.col.before,
            'vline_after': self.col.after,
        }

    # save multicolumn width in case it's the longest row
    def add_span_width(self, cell, span_wdith):
        if cell not in self.cell_span:
            self.save_cell_span(cell)
        self.cell_span[cell]['span_width'] = span_wdith

    def add_vline_pos(self, x_pos, ID):
        self.vline_pos.append(VLinePosition(x_pos, ID))


class TableCellConstraint:
    def __init__(self):
        self.max_width = None
        self.init_cell_x = -1
        self.init_row_y = -1
        self.last_min_y = None
        self.cell_objects = []

    def set_init_pos(self, width, height):
        self.init_cell_x = width
        self.init_row_y = height
        self.last_min_y = None

    def set_column_width(self, scale, columns, col):
        if len(columns) <= col:
            return

        # save width constraint if it's positive
        p_width = columns[col].width
        if p_width > 0:
            self.max_width = self.init_cell_x + p_width * scale

    def reset_cell_constraint(self):
        self.max_width = None
        self.init_cell_x = -1
        self.init_row_y = -1
        self.last_min_y = None
        self.cell_objects.clear()


class TableState:
    def __init__(self, parent_coll, init_params):
        self.parent_coll = parent_coll
        self.init_params = init_params
        self.table_coll = ''
        self.obj_array = [[]]
        self.align = TableAlignment()
        self.hline = TableHorizontalLines()
        self.multi = TableMultiCell()

    # returns the index of the current row
    def get_row_num(self) -> int:
        return len(self.obj_array) - 1

# ------------------
# MATH MODE CLASSES
# ------------------

class Levels:
    def __init__(self, frac_array):
        self.ei_array = []
        self.frac_array = frac_array
        self.sqrt = False
        self.sym_name = ''


# class for index and exponent
class ExpIxState:
    def __init__(self, parent_coll, init_params, sym_name):
        self.parent_coll = parent_coll
        self.init_params = init_params
        self.eicoll = ''
        self.eicoll2 = ''
        self.sym_name = sym_name
        self.width = 0


class FractionState:
    def __init__(self, parent_coll, init_params):
        self.parent_coll = parent_coll
        self.init_params = init_params
        self.ncoll = ''
        self.dcoll = ''
        self.nwidth = 0.0
        self.dwidth = 0.0


class SqrtState:
    def __init__(self, parent_coll, init_params):
        self.parent_coll = parent_coll
        self.init_params = init_params
        self.sqcoll = ''


class MatrixState:
    def __init__(self, parent_coll, init_params):
        self.parent_coll = parent_coll
        self.init_params = init_params
        self.size = MatrixSize()
        self.mx_coll = ''
        self.obj_array = [[]]
        self.brackets = 'matrix'

    # returns the index of the current row
    def get_row_num(self) -> int:
        return len(self.obj_array) - 1


# class for matrix dimensions
class MatrixSize:
    def __init__(self):
        self.min_x = -1
        self.min_y = -1
        self.max_x = -1
        self.max_y = -1

# ---------------
# FONT FUNCTIONS
# ---------------

FONT_CACHE = {}

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
    text_data = bpy.data.curves.new(name="H_tmp", type='FONT')
    text_data.font = font
    text_data.body = 'H'

    # create temporary H object
    h_obj = bpy.data.objects.new("H_tmp", text_data)
    context.collection.objects.link(h_obj)

    depsgraph = context.evaluated_depsgraph_get()
    h_obj_eval = h_obj.evaluated_get(depsgraph)

    # base blender font size is 0.6820 (for H)
    size = 0.6820 / h_obj_eval.dimensions.y

    bpy.data.objects.remove(h_obj, do_unlink=True)
    bpy.data.curves.remove(text_data)

    return round(size, 4)
