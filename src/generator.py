# ---------------------------------------------------------------------------
# File name   : generator.py
# Created By  : Katarina Strenkova
# ---------------------------------------------------------------------------

import bpy

from bpy_extras.object_utils import object_data_add  # add sqrt symbol
from mathutils import Vector  # vertices

from .syntax_utils import change_font
from .data.characters_db import *


# function generates text in given font
def gen_text(text, font_info, collection, line, math_mode=None):
    text_data = bpy.data.curves.new("Text", type='FONT')
    text_data.body = text

    if len(font_info) > 0:
        text_data.font = font_info['font']
        text_data.size = font_info['size']

    # changing size for bigger symbols, e.g. sum, integral
    if text in unicode_chars_big.values() and math_mode == 'display':
        text_data.size *= 1.5

    text_obj = bpy.data.objects.new("Text", text_data)
    bpy.data.collections[collection].objects.link(text_obj)
    bpy.context.view_layer.objects.active = text_obj

    # add object to current line
    line.line_objs.append(text_obj)

    return text_obj


# function sets the position of an object
def gen_set_position(obj, param):
    # scale object
    obj.scale.x = param.scale
    obj.scale.y = param.scale

    obj.location.x = param.width  # move by width (x)
    obj.location.y = param.height  # move by height (y)
    obj.location.z = 0.0


# function moves the object and sets the starting width
def gen_move_position(obj, param):
    gen_set_position(obj, param)

    # get corners of bounding box
    bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    obj_dimension = bbox[4].x * param.scale
    param.width += obj_dimension + (0.1 * param.scale)  # space


# function creates a new text object with given value and font,
# then moves it according to context
def gen_text_object(param, defaults, text, font_type, levels=None, symbol=None):
    # generate text into current collection
    obj = gen_text(text, change_font(font_type), defaults.current_coll, param.line, defaults.math_mode)

    if levels:
        # calculate level for math mode
        gen_calculate(param, defaults.text_scale, levels, symbol)
    else:
        # set line height for text mode
        param.height = param.line.height

    # set object position
    gen_move_position(obj, param)


# function calculates and adjusts the height for new line
def gen_adjust_new_line(param, base_coll, line_space, init_width=0.0):
    # no objects have been generated yet
    if len(bpy.data.collections[base_coll].all_objects) == 0:
        return

    # multiple new lines in the row
    if len(param.line.line_objs) == 0:
        param.line.min_y -= line_space * param.scale
        param.line.height = param.line.min_y - line_space * param.scale
        param.width = init_width
        return

    # save all minimum y
    all_min_y = []

    if param.line.table_min_y is not None:
        all_min_y.append(param.line.table_min_y - BASE_SPACE * param.scale)

        # center all objects according to the table
        for obj in param.line.line_objs:
            obj.location.y -= (param.line.height - param.line.table_min_y) / 2.0

    if param.line.min_y is not None:
        # calculate overflow
        max_y = gen_bound_for_array(param.line.line_objs, 'y', 'max')
        lmin_y = param.line.min_y  # lowest point of last row
        overflow = max_y - lmin_y if (max_y > lmin_y) else 0

        # move objects down
        if overflow > 0:
            for obj in param.line.line_objs:
                obj.location.y -= overflow

    # get real and expected lowest point
    real_min_y = gen_bound_for_array(param.line.line_objs, 'y', 'min')
    expected_min_y = param.line.height - (SMALL_SPACE * line_space * param.scale)

    # save the lowest point
    all_min_y.extend([real_min_y, expected_min_y])
    param.line.min_y = min(all_min_y)

    # reset line objects
    param.line.line_objs.clear()

    param.line.height = param.line.min_y - line_space * param.scale
    param.width = init_width


# function calculates and adjusts the height for new line in one table cell
def gen_new_line_in_cell(param, cell_constraint, line_space):
    if cell_constraint.last_min_y is not None:
        # calculate overflow
        max_y = gen_bound_for_array(cell_constraint.cell_objects, 'y', 'max')
        lmin_y = cell_constraint.last_min_y  # lowest point of last row
        overflow = max_y - lmin_y if (max_y > lmin_y) else 0

        # move objects down
        if overflow > 0:
            for obj in cell_constraint.cell_objects:
                obj.location.y -= overflow

    # get real and expected lowest point
    real_min_y = gen_bound_for_array(cell_constraint.cell_objects, 'y', 'min')
    expected_min_y = param.line.height - (SMALL_SPACE * line_space * param.scale)

    # save the lowest point
    cell_constraint.last_min_y = min(real_min_y, expected_min_y)

    # reset cell constraint objects
    cell_constraint.cell_objects.clear()

    param.line.height = cell_constraint.last_min_y - line_space * param.scale
    param.width = cell_constraint.init_cell_x


# function wraps objects in cell that has width constraint
# the return value signals whether whitespace should be consumed
def gen_wrap_obj_in_cell(param, defaults, cell_constraint):
    # return if there is no cell constraint
    if cell_constraint.max_width is None:
        return False

    # save current object
    cell_constraint.cell_objects.append(defaults.context.active_object)

    # return if the object maximum is lower than the cell constraint
    current_max_x = gen_bound_for_array([defaults.context.active_object], 'x', 'max')
    if current_max_x < cell_constraint.max_width:
        return False

    # set new line for next objects in this table cell
    gen_new_line_in_cell(param, cell_constraint, defaults.line_height)
    return True


# function generates line object
def gen_line_object(context, param, collection, x_pos, y_pos, line_length, axis='x'):
    # calculate line thickness
    line_thickness = LINE_THICKNESS * param.scale

    if axis == 'x':
        verts = [
            Vector((0.0, -line_thickness, 0.0)),
            Vector((0.0, line_thickness, 0.0)),
            Vector((line_length, line_thickness, 0.0)),
            Vector((line_length, -line_thickness, 0.0))
        ]
    else:
        verts = [
            Vector((-line_thickness, 0.0, 0.0)),
            Vector((line_thickness, 0.0, 0.0)),
            Vector((line_thickness, line_length, 0.0)),
            Vector((-line_thickness, line_length, 0.0))
        ]

    edges = []
    faces = [[0, 1, 2, 3]]

    mesh = bpy.data.meshes.new(name="Line")
    mesh.from_pydata(verts, edges, faces)
    object_data_add(context, mesh)

    # location of line
    line_obj = context.active_object
    line_obj.location = Vector((x_pos, y_pos, 0.0))

    # save line into the current collection
    gen_object_to_collection(line_obj, collection)


# function creates new collection
def gen_new_collection(coll_name, parent_coll):
    # add new collection
    collection = bpy.data.collections.new(coll_name)
    bpy.data.collections[parent_coll].children.link(collection)
    return collection.name


# function sets the active collection
def gen_set_active_collection(base_coll, current_coll):
    view_layer = bpy.context.view_layer
    collection = view_layer.layer_collection.children[base_coll].children[current_coll]
    view_layer.active_layer_collection = collection


# function joins collections into parent collection and removes child collection
def gen_join_collections(coll_name, parent_coll_name):
    coll = bpy.data.collections.get(coll_name)
    parent_coll = bpy.data.collections.get(parent_coll_name)

    if coll is None or parent_coll is None:
        return

    # join all objects into one parent collection
    for obj in list(coll.objects):
        parent_coll.objects.link(obj)
        coll.objects.unlink(obj)

    # remove child collection
    bpy.data.collections.remove(coll)


# function sets a new active collection
def gen_activate_collection(collection):
    layer_collection = bpy.context.view_layer.layer_collection
    for layer in layer_collection.children:
        if layer.name == collection:
            bpy.context.view_layer.active_layer_collection = layer


# function adds object to a specific collection
def gen_object_to_collection(obj, collection):
    # unlink from all collections
    for coll in obj.users_collection:
        coll.objects.unlink(obj)

    # link object into the correct collection
    bpy.data.collections[collection].objects.link(obj)


# function generates square root symbol
def gen_sqrt_sym(context, collection):
    # symbol vertices
    verts = [
        Vector((-0.5266461968421936, -0.13621671915054321, 0.0)),
        Vector((-0.40451911091804504, -0.21025631248950958, 0.0)),
        Vector((-0.3643374443054199, -0.13621671915054321, 0.0)),
        Vector((-0.15997552871704102, -0.7838898515701294, 0.0)),
        Vector((-0.15997552871704102, -0.6396166300773621, 0.0)),
        Vector((0.36744120717048645, 0.35296740531921387, 0.0)),
        Vector((0.32928138971328735, 0.4122579336166382, 0.0)),
        Vector((0.4593656659126282, 0.35296740531921387, 0.0)),
        Vector((0.4593656659126282, 0.4122579336166382, 0.0))
    ]

    edges = []
    faces = [[0, 1, 2], [1, 2, 4, 3], [4, 3, 5, 6], [5, 6, 8, 7]]

    mesh = bpy.data.meshes.new(name="Sqrt")
    mesh.from_pydata(verts, edges, faces)
    object_data_add(context, mesh)

    origin_offset = Vector((-0.5266461968421936, -0.8238898515701294, 0.0))

    # offset all mesh vertices
    for vert in mesh.vertices:
          vert.co -= origin_offset

    # move the object to keep the object in the same position
    sqrt_obj = context.active_object
    sqrt_obj.location += origin_offset

    # recalculate normals in editmode
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.editmode_toggle()

    sqrt_obj = context.active_object

    # save sqrt symbol into the current collection
    gen_object_to_collection(sqrt_obj, collection)

    return sqrt_obj


# function moves sqrt symbol according to given parameters
def gen_sqrt_move(obj, param, sqrt_param, move):
    # position sqrt
    param.height -= 0.25 * param.scale
    gen_set_position(obj, param)
    param.height += 0.25 * param.scale

    # apply scale
    bpy.ops.object.transform_apply(scale=True, location=False, rotation=False)

    # don't modify square root symbol
    if not move:
        return

    # data of created sqrt symbol
    obj_data = obj.data
    vertices = obj_data.vertices

    # common parameters
    text_height = param.height - (SMALL_SPACE * param.scale)

    # find vertex extremes
    x_coords = [v.co.x for v in vertices]
    y_coords = [v.co.y for v in vertices]
    max_x = max(x_coords)
    max_y = max(y_coords)
    min_y = min(y_coords)

    # changing length of the upper line of sqrt
    for v in vertices:
        if v.co.x == max_x:
            v.co.x = sqrt_param['x_pos'] - param.width  # x position

    line_size_top = SQRT_LINE_TOP * param.scale  # size of upper line
    move_by_top = sqrt_param['y_max'] - text_height + (SMALL_SPACE * param.scale)  # y location and space

    # if height of sqrt is not correct
    if (max_y - 0.06) <= move_by_top:
        threshold_top = max_y - (0.06 * param.scale)

        # changing height of sqrt symbol
        for v in vertices:
            if v.co.y == max_y:
                v.co.y = move_by_top + line_size_top
            elif v.co.y >= threshold_top:
                v.co.y = move_by_top

    line_size_bottom = SQRT_LINE_BOTTOM * param.scale  #  space between lowest points
    move_by_bottom = sqrt_param['y_min'] - text_height

    # if low point of sqrt is not correct
    if min_y >= move_by_bottom:
        threshold_bottom = min_y + (0.15 * param.scale)

        # changing lowest point of sqrt symbol
        for v in vertices:
            if v.co.y == min_y:
                v.co.y = move_by_bottom
            elif v.co.y <= threshold_bottom:
                v.co.y = move_by_bottom + line_size_bottom


# function generates fraction line
def gen_frac_line(context, param, collection, line_length):
    x_pos = param.width
    y_pos = param.height + BASE_SPACE * param.scale
    line_end = line_length - param.width + MIN_SPACE * param.scale
    gen_line_object(context, param, collection, x_pos, y_pos, line_end)


# function moves objects in fraction
def gen_frac_move(param, collection, mode):
    # get highest or lowest point in collection
    y = gen_bound(collection, 'y', 'max') if mode == "den" else gen_bound(collection, 'y', 'min')
    extra_padding = (MIN_SPACE if mode == "den" else 0.6) * param.scale

    # early return when no objects
    if y is None:
        return

    # select and move all objects in denominator
    for obj in bpy.data.collections[collection].all_objects:
        obj.location.y += param.height - y + extra_padding


# helper function to get the fraction level scale
def get_frac_scale(levels, text_scale, scale_low, scale_nested):
    level = len(levels.frac_array)

    # no fraction or base level fraction
    if level <= 1:
        return text_scale

    # display fraction command
    if levels.frac_array[-1] == 'dfrac':
        return text_scale

    # first level fraction or fraction before was dfrac
    if level == 2 or (levels.frac_array[-2] == 'dfrac'):
        return scale_low

    # second level fraction
    return scale_nested


# function calculates the scaling and height of text
def gen_calculate(param, text_scale, levels, symbol=None):
    # height factors
    first_exp = 0.75
    nested_exp = 0.5
    first_ix = 0.5
    nested_ix = 0.25

    # scale factors
    scale_low = 0.65 * text_scale
    scale_nested = 0.45 * text_scale

    lvl_exp = 0  # exponent lvl
    lvl_ix = 0  # index lvl

    # starting height is line height and scale is user given scale
    param.height = param.line.height
    param.scale = get_frac_scale(levels, text_scale, scale_low, scale_nested)

    # iterating through array of exponents and indexes
    for item in levels.ei_array:
        is_base_level = (lvl_exp + lvl_ix) == 0

        # scale based on level of index/exponent
        if is_base_level and ((len(levels.frac_array) < 2) or (levels.frac_array[-1] == 'dfrac')):
            param.scale = scale_low
        else:
            param.scale = scale_nested

        # adding number of exponent or index
        if item == "exp":
            lvl_exp += 1
            factor = first_exp if lvl_exp == 1 else nested_exp
            param.height += factor * param.scale
        else:
            lvl_ix += 1
            factor = first_ix if lvl_ix == 1 else nested_ix
            param.height -= factor * param.scale

    # special vertical move for large symbols
    if symbol in unicode_chars_big.values():
        param.height -= SMALL_SPACE * text_scale  # move lower


# function moves sum symbol according to given parameters
def gen_move_sum(param, collection, sum_name):
    sum_symbol = bpy.data.objects[sum_name]

    # get corners of bounding box
    bbox = [sum_symbol.matrix_world @ Vector(corner) for corner in sum_symbol.bound_box]

    # parameters of objects in collection
    min_x = gen_bound(collection, 'x', 'min')
    min_y = gen_bound(collection, 'y', 'min')
    max_y = gen_bound(collection, 'y', 'max')

    # iterate through objects
    op_array = []
    for obj in bpy.data.collections[collection].all_objects:
        # add object to array
        op_array.append(obj.name)
        # move object depending on index or exponent mode
        obj.location.x += bbox[0].x - min_x
        if "ExponentCollection" in collection:
            obj.location.y += bbox[2].y - min_y + BASE_SPACE * param.scale
        else:
            obj.location.y += bbox[0].y - max_y - BASE_SPACE * param.scale

    # center text above sum symbol
    gen_center_sum(collection, bbox[4].x)  # sum width


# function centers exponent and index for sum symbol
def gen_center_sum(collection, sum_width):
    # calculate movement size
    exp_ix_width = gen_bound(collection, 'x', 'max')
    move_by = (sum_width - exp_ix_width) / 2.0

    # move all objects
    for obj in bpy.data.collections[collection].all_objects:
        obj.location.x += move_by


# move sum symbol if index or exponent is longer then symbol
def gen_fin_sum(sum_name, up_collection, down_collection):
    sum_symbol = bpy.data.objects[sum_name]

    # get corners of bounding box
    bbox = [sum_symbol.matrix_world @ Vector(corner) for corner in sum_symbol.bound_box]
    sum_width = bbox[4].x

    # find biggest width
    fin_width = max(
        gen_bound(up_collection, 'x', 'max') or 0.0,
        gen_bound(down_collection, 'x', 'max') or 0.0,
        sum_width
    )

    diff = fin_width - sum_width

    # index or exponent is longer than sum symbol
    if diff > 0:
        obj_move = [sum_symbol]

        # get all objects in sub/superscript
        if up_collection == down_collection:
          obj_move.extend(bpy.data.collections[down_collection].all_objects)
        else:
          obj_move.extend(bpy.data.collections[up_collection].all_objects)
          obj_move.extend(bpy.data.collections[down_collection].all_objects)

        # move all objects
        for obj in obj_move:
            obj.location.x += diff

    return fin_width + diff


# function centers objects on x axis
def gen_center(obj1, obj2, collection):
    # find wider text
    diff = obj1 - obj2 if (obj1 > obj2) else obj2 - obj1
    move_by = diff / 2.0  # space between x positions div 2

    # move all objects
    for obj in bpy.data.collections[collection].all_objects:
        obj.location.x += move_by


# calculate the extreme for set axis and type (min/max)
def gen_calculate_bound(objects, axis, ftype):
    bpy.ops.object.select_all(action='DESELECT')  # deselect all objects

    # determine which corner index to check
    if axis == 'x' and ftype == 'max':
        corner_index = 4
    elif axis == 'y' and ftype == 'max':
        corner_index = 2
    else:
        corner_index = 0

    # save position of all objects
    positions = []
    for obj in objects:
        obj.select_set(True)
        bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        positions.append(getattr(bbox[corner_index], axis))

    func = max if ftype == 'max' else min
    return func(positions)  # return max or min from all positions


# function returns the extreme for an array of objects
def gen_bound_for_array(objects, axis, ftype):
    if not objects:
        return None

    # update object placement
    bpy.context.view_layer.update()

    return gen_calculate_bound(objects, axis, ftype)


# function returns the extreme for objects in a collection
def gen_bound(coll_name, axis, ftype):
    coll = bpy.data.collections.get(coll_name)
    objects = coll.all_objects

    # early return if no objects
    if not objects:
        return None

    return gen_calculate_bound(objects, axis, ftype)


# function returns the max width of the given column
def get_max_column_width(obj_array, col, max_width, multi=None):
    for i, row in enumerate(obj_array):
        # check for multicolumn
        cell_span = getattr(multi, 'cell_span', {})
        cell = cell_span.get((i, col), {})
        extra_col = cell.get('col_span', 1) - 1

        if col < len(row) and extra_col > 0:
            cell_width = gen_bound(row[col], 'x', 'max')
            if cell_width is not None:
                # push current width into last multicolumn cell
                last_col = (i, col + extra_col)
                multi.add_span_width(last_col, cell_width)
            continue

        # normal cell
        if col < len(row):
            cell_width = gen_bound(row[col], 'x', 'max')
            if cell_width is not None:
                max_width = max(max_width, cell_width)

        # check whether multicolumn cell is not the wider than current column
        if 'span_width' in cell:
            max_width = max(max_width, cell['span_width'])

    return max_width


# function returns the max height of the given row
def get_min_row_height(row, max_col, min_height):
      for col in range(max_col):
          if col < len(row):
              collection = row[col]
              cell_bottom = gen_bound(collection, 'y', 'min')
              if cell_bottom is not None:
                min_height = min(min_height, cell_bottom)

      return min_height


# function returns the max height of the given row
def get_max_row_height(row, max_col, max_height):
    for col in range(max_col):
        if col < len(row):
            collection = row[col]
            cell_height = gen_bound(collection, 'y', 'max')
            if cell_height is not None:
                max_height = max(max_height, cell_height)

    return max_height


# function moves the next column horizontally right
def gen_move_column(obj_array, col, offset, version='relative'):
    for row in obj_array:
        if col < len(row):
            collection = row[col]

            if version == 'relative':
                # find current minimum position
                min_x = gen_bound(collection, 'x', 'min')
                move_by = offset - min_x if min_x is not None else 0.0
            else:
                # move by constant amount
                move_by = offset

            # move all objects in this cell
            for obj in bpy.data.collections[collection].all_objects:
                obj.location.x += move_by


# function moves the next row vertically down
def gen_move_row(row, num_columns, move_by):
      for col in range(num_columns):
          if col < len(row):
              collection = row[col]
              for obj in bpy.data.collections[collection].all_objects:
                  obj.location.y -= move_by


# function calculates horizontal offset and moves all objects in the collection
def apply_alignment_x(collection, alignment, max_width):
    # get max width of objects in current collection
    cell_width = gen_bound(collection, 'x', 'max') or 0.0

    # calculate the horizontal movement based on alignment
    if alignment == 'c':
        move_by = (max_width - cell_width) / 2
    elif alignment == 'r':
        move_by = max_width - cell_width
    else:
        move_by = 0  # alignment 'l' is the default

    # move all objects in this cell
    if move_by != 0:
        for obj in bpy.data.collections[collection].all_objects:
            obj.location.x += move_by


# function aligns objects horizontally in the current column
def gen_column_cells_align_x(obj_array, col, max_col_width, alignment='c', cell_span={}):
    for i, row in enumerate(obj_array):
        if col < len(row):
            # ignore alignment for multicolumn
            cell = cell_span.get((i, col), {})
            if cell.get('col_span', 1) > 1:
                continue

            collection = row[col]
            apply_alignment_x(collection, alignment, max_col_width)


# function aligns content of cells horizontally for multicolumn command
def gen_multicolumn_cells_align_x(obj_array, param, align, cell_span):
    for (row, col), span_info in cell_span.items():
        col_span = span_info['col_span']
        col_align = span_info['col_align']

        # process multicolumn only
        if col_span == 1:
            continue

        # last column of multicolumn span
        last_col = col + col_span

        # get current cell
        if row < len(obj_array) and last_col < len(obj_array[row]):
            # get width of the last column without padding
            total_width = align.column_width[last_col] - GRID_SPACE * param.scale

            collection = obj_array[row][col]
            apply_alignment_x(collection, col_align, total_width)


# funtion moves the current column for vertical lines
# that will be generated before it
def gen_move_column_for_vline(obj_array, param, col, align, x_pos):
    # number of vertical lines before current column
    line_count = align.vline[col]

    # skip if no lines
    if line_count == 0:
        return

    # save position and create space
    for _ in range(line_count):
        align.add_vline_pos(x_pos, col)
        x_pos += SMALL_SPACE * param.scale

    # move next column to make space for vertical lines
    vline_space = (SMALL_SPACE * (line_count - 1) + LINE_THICKNESS * line_count) * param.scale
    gen_move_column(obj_array, col, vline_space, 'const')

    # return used space for multicolumn vline calculation
    return vline_space - line_count * LINE_THICKNESS * param.scale


# function moves the current cell for vertical lines
def gen_move_multicolumn_for_vline(collection, param, row, multi, span_info, x_pos, version):
    # number of vertical lines
    line_count = span_info[f'vline_{version}']

    # skip if no lines
    if line_count == 0:
        return

    direction = 1 if version == 'before' else -1

    # save position and create space
    for _ in range(line_count):
        multi.add_vline_pos(x_pos, row)
        x_pos += (SMALL_SPACE * direction) * param.scale

    # early return for vertical lines at the end of column
    if version == 'after':
        return

    # move the cell content to make space for vertical lines
    vline_space = (SMALL_SPACE * (line_count - 1) + LINE_THICKNESS * line_count) * param.scale
    for obj in bpy.data.collections[collection].all_objects:
        obj.location.x += vline_space


# function moves multicolumn when it intersects with vertical lines
def process_multicolumn_vlines(obj_array, param, multi, cell_span, col, total_space):
    for (r, c), span_info in cell_span.items():
        col_span = span_info.get('col_span', 1)

        if col_span == 1:
            continue

        collection = obj_array[r][c]

        # Check if multicolumn starts at the target column
        if c == col:
            gen_move_multicolumn_for_vline(collection, param, r, multi, span_info, total_space, 'before')

        # Check if multicolumn ends right before the target column
        elif (c + col_span) == col:
            gen_move_multicolumn_for_vline(collection, param, r, multi, span_info, total_space, 'after')


# function saves positions of vertical lines after the last column
def gen_last_column_vline(col, align, x_pos):
    # number of vertical lines after current column
    line_count = align.vline[col+1]

    # skip if no lines
    if line_count == 0:
        return

    # save position of vertical lines
    for _ in range(line_count):
        align.add_vline_pos(x_pos, col+1)
        x_pos += SMALL_SPACE


# function aligns cells horizontally for matrix
def gen_matrix_align_x(obj_array, param):
    prev_col_width = param.width
    padding = GRID_SPACE * param.scale

    # calculate the max number of columns
    max_col = max(len(row) for row in obj_array)

    for col in range(max_col):
        # find max width for the current column
        max_col_width = get_max_column_width(obj_array, col, prev_col_width)

        # add extra padding for empty column
        is_empty_column = (prev_col_width == max_col_width)
        extra_padding = (2 * padding) if is_empty_column else 0

        # calculate spacing for the next column
        prev_col_width = max_col_width + padding + extra_padding

        # move objects in next collumn
        if (col + 1) < max_col:
            gen_move_column(obj_array, col + 1, prev_col_width)

        # center column content horizontally
        gen_column_cells_align_x(obj_array, col, max_col_width)


# function aligns cells horizontally by alignment type
def gen_table_align_x(obj_array, param, align, multi):
    # initialize parameters
    prev_col_width = param.width
    padding = GRID_SPACE * param.scale
    cell_span = getattr(multi, 'cell_span', {})

    # calculate the max number of columns
    max_col = max(len(row) for row in obj_array)

    # save the starting width for cline command
    align.column_width.append(param.width)

    for col in range(max_col):
        # check for any vertical lines in current column
        vline_space = 0
        if len(align.vline) > col:
            vline_space = gen_move_column_for_vline(obj_array, param, col, align, prev_col_width)

        # process multicolumns
        total_space = prev_col_width + vline_space
        process_multicolumn_vlines(obj_array, param, multi, cell_span, col, total_space)

        # add padding before the column
        gen_move_column(obj_array, col, padding, 'const')

        # find max width for the current column
        max_col_width = get_max_column_width(obj_array, col, prev_col_width, multi)

        # add extra padding for empty column
        is_empty_column = (prev_col_width == max_col_width)
        extra_padding = (2 * padding + vline_space) if is_empty_column else 0

        # calculate spacing for the next column
        prev_col_width = max_col_width + padding + extra_padding

        # save each column width for cline command
        align.column_width.append(prev_col_width)

        if len(align.vline) > (col + 1) and (col + 1) == max_col:
            # check for vertical line after the last column
            gen_last_column_vline(col, align, prev_col_width)

            # check if multicolumn ends on the last column
            process_multicolumn_vlines(obj_array, param, multi, cell_span, col + 1, prev_col_width)

        # move objects in next collumn
        if (col + 1) < max_col:
            gen_move_column(obj_array, col + 1, prev_col_width)

        # align cells horizontally based on alignment type
        gen_column_cells_align_x(obj_array, col, max_col_width, align.columns[col].type, cell_span)

    # special alignment for multicolumn
    gen_multicolumn_cells_align_x(obj_array, param, align, cell_span)


# function aligns cells vertically for multirow command
def gen_multirow_cells_align_y(obj_array, align, cell_span):
    max_col = max(len(row) for row in obj_array)

    for i, row in enumerate(obj_array):
        for col in range(max_col):
            cell = cell_span.get((i, col), {})
            row_span = cell.get('row_span', 1)

            # process multirow only
            if row_span == 1:
                continue

            collection = row[col]
            last_row = i + row_span - 1

            # get the y position of first and last row of multirow
            _, y_first = align.row_y[i]
            _, y_last = align.row_y[last_row]

            # move objects lower
            for obj in bpy.data.collections[collection].all_objects:
                obj.location.y += (y_last - y_first) / 2.0


# function centers cells in matrix vertically
def gen_matrix_align_y(obj_array, param):
    # calculate the max number of columns
    max_col = max(len(row) for row in obj_array)
    prev_max_height = param.height
    padding = SMALL_SPACE * param.scale

    # initialize row minimum
    min_row_height = None

    for row in obj_array:
        # find max height for the current row
        max_row_height = get_max_row_height(row, max_col, prev_max_height)
        prev_max_height = max_row_height

        # check for first iteration
        if min_row_height is not None:
            # move row if its highest point cuts into the upper row
            if max_row_height > min_row_height:
                move_by = max_row_height - min_row_height + padding
                gen_move_row(row, max_col, move_by)

        # find min height for the current row
        min_row_height = get_min_row_height(row, max_col, max_row_height)


# function aligns cells for table vertically to center
def gen_table_align_y(obj_array, align, multi):
    cell_span = getattr(multi, 'cell_span', {})

    # align content of multirow
    gen_multirow_cells_align_y(obj_array, align, cell_span)

    # save multicolumn ranges per row
    remove_ranges = {}
    for (r, c), span_info in cell_span.items():
        if span_info['col_span'] > 1:
            start_col = c + 1
            end_col = c + span_info['col_span']

            # add new row info if not present
            if r not in remove_ranges:
                remove_ranges[r] = []

            # save range of multicolumn
            remove_ranges[r].append((start_col, end_col))

    for i, _ in enumerate(obj_array):
        # get list of ranges
        row_ranges = remove_ranges.get(i, [])

        # save vertical lines for normal columns
        for vline in align.vline_pos:
            # check whether vline should be hidden
            is_hidden = any(start <= vline.ID <= end for start, end in row_ranges)

            # save y position for non-hidden vertical lines
            if not is_hidden:
                vline.y_pos.append(align.row_y[i])

        # save vertical lines for multicolumn
        for vline in multi.vline_pos:
            if vline.ID == i:
                vline.y_pos.append(align.row_y[i])


# TODO [fix] vmatrix and Vmatrix have tricky space after left bracket
# function generates matrix brackets
def gen_brackets(context, bracket, param, collection, size):
    # determine left or right bracket
    is_left = (size.max_x == -1)
    x = size.min_x if is_left else size.max_x

    # scale bracket object
    matrix_height = size.max_y - size.min_y
    scale = (matrix_height + 0.5 * param.scale) / bracket.dimensions.y
    bracket.scale.x = scale / 3.0
    bracket.scale.y = scale

    # force update after scaling
    context.view_layer.update()

    # calculate the offset of bracket origin
    bbox = [bracket.matrix_world @ Vector(corner) for corner in bracket.bound_box]
    bracket_min_y = abs(bbox[0].y) - 0.15
    offset = size.min_y + bracket_min_y

    # move bracket object
    bracket.location = (x, offset, 0)

    # left bracket
    if is_left:
        for obj in bpy.data.collections[collection].all_objects:
            # move all objects besides bracket
            if obj.name != bracket.name:
                obj.location.x += 1.5 * bracket.dimensions.x

        # save bracket_width
        size.bracket_width = bracket.dimensions.x


# function centers matrix
def gen_matrix_center(collection, size, base_line):
    # calculate center location
    center_loc = (size.max_y + size.min_y) / 2.0
    offset = center_loc + abs(base_line)

    # center matrix into row
    for obj in bpy.data.collections[collection].all_objects:
        obj.location.y -= offset


# function gets level of nesting for itemize/enumerate
def get_nest_level(nest_array, env_type):
    nest_lvl = 0
    for item in nest_array:
        if item == env_type:
            nest_lvl += 1

    return nest_lvl


# function return default bullet point values based on nested level
def get_bullet_default(level):
    bullet_types = [
        '\u2022',
        '\u2013',
        '\u2217',
        '\u00B7'
    ]

    # calculate index based on level
    index = min(level, len(bullet_types)) - 1
    return bullet_types[index]


# function returns roman numbers
def get_roman(num):
    lookup = [
        (100, 'c'), (90, 'xc'), (50, 'l'), (40, 'xl'),
        (10, 'x'), (9, 'ix'), (5, 'v'), (4, 'iv'), (1, 'i'),
    ]

    item = ''
    for (value, roman) in lookup:
        (res, num) = divmod(num, value)
        item += roman * res
    return item


# function returns default numbering based on nested level
def get_numbering_default(level, index):
    if level == 1:
        item = str(index) + '.'

    elif level == 2:
        char_code = 97 + ((index - 1) % 26)  # a, b, c, ...
        item = '(' + chr(char_code) + ')'

    elif level == 3:
        item = get_roman(index) + '.'

    else:
        char_code = 65 + ((index - 1) % 26)  # A, B, C, ...
        item = chr(char_code) + '.'

    return item


# function calculates positions around bullet point
def gen_bullet_point(objects, param, defaults, nest_lvl):
    if not objects:
        return

    # calculate spacing based on last object
    last_obj = objects[-1]
    bbox = [last_obj.matrix_world @ Vector(corner) for corner in last_obj.bound_box]
    obj_dimension = bbox[4].x * param.scale
    nested_space = nest_lvl * defaults.block_space * param.scale
    param.width = (nested_space - obj_dimension)  # space before bullet point

    # move all objects
    for obj in objects:
        gen_move_position(obj, param)

    param.width += BASE_SPACE * param.scale  # space after bullet point


# function parses width string and updates target object
def parse_table_width(target, content, msg, is_multirow=False):
    # multirow special case
    if is_multirow:
        if content == '*':
            return ""
    else:
        # check alignment type
        if getattr(target, 'type', '') not in ['p', 'm', 'b']:
            return f"Alignment '{target.type}' does not support width specification!"

    for u in units:
        if content.endswith(u):
            content = content[:-len(u)]
            target.unit = u
            break

    if len(target.unit) == 0:
        return f"Invalid unit '{content}' in {msg} width specification!"

    try:
        target.width = float(content)
    except ValueError:
        return f"Invalid numeric value '{content}' in {msg} width specification!!"

    # no errors
    return ""


# function parses string that describes \cline range
def parse_cline_range(range):
    # check for hyphen in the cline range
    if '-' not in range:
        return "", f"Missing hyphen in \cline! Expected format 'start-end', got: '{range}.'"

    items = range.split('-')

    if len(items) != 2:
        return "", "Too many hyphens in \cline! Please provide exactly two numbers."

    try:
        # convert both values into integers
        start = int(items[0])
        end = int(items[1])
    except ValueError:
        return "", f"Both values in \cline must be numbers. Got: '{items[0]}' and '{items[1]}'"

    # check if first number is smaller than the second one
    if start > end:
        return "", f"In \cline, start column ({start}) cannot be greater than end column ({end})."

    # check if starting number is bigger than 1
    if start < 1:
        return "", f"In \cline, column numbers must be 1 or greater. Got: {start}"

    return (start, end), ""


# TODO [feature] Make b{} and m{} alignment work
# function parses multicolumn alignment into vertical lines and alignment
def parse_multicol_alignment(multi, content):
    if not content:
        return "Alignment in \\multicolumn command is empty!"

    # save the alignment and number of vertical lines
    multi.col.before = len(content) - len(content.lstrip('|'))
    multi.col.after = len(content) - len(content.rstrip('|'))
    alignment = content.strip('|')

    # check format
    if len(alignment) != 1:
          return f"Invalid alignment format '{content}'! Expected: |...|<letter>|...|"

    # check the alignment type
    if alignment not in table_alignments:
        return f"Unsupported alignment '{alignment}' in \\multicolumn command! Use one of: {', '.join(table_alignments)}"

    multi.col.align = alignment
    return ""


# function saves the span number for multicolumn and multirow commands
def get_multi_span_number(multi, action, content):
    try:
        # check the span number is integer and save it
        span = int(content)
        if 'COL' in action:
            multi.col.span = span
        else:
            multi.row.span = span
        return ""

    except ValueError:
        cmd_name = '\\multicolumn' if 'COL' in action else '\\multirow'
        err = f"Invalid integer value '{content}' in {cmd_name} specification!"
        return err


# function saves info about multicolumn command and adds placeholder collections
def save_multicol_info(ts):
    # skip if there is no multicolumn/multirow info
    if ts.multi.col.span == 1 and ts.multi.row.span == 1:
        return

    row = ts.get_row_num()
    col = len(ts.obj_array[row]) - 1
    ts.multi.save_cell_span((row, col))
    ts.multi.row.reset_row_span()

    # add placeholder collections for multicolumn
    extra_col = ts.multi.col.span - 1
    for _ in range(extra_col):
        placeholder = gen_new_collection("TableCellPlaceholder", ts.table_coll)
        ts.obj_array[row].append(placeholder)
    ts.multi.col.reset_col_span()


# function removes the last row if it only contains one empty collection
def gen_cleanup_last_row(obj_array):
    if not obj_array:
        return

    # get last row object
    last_row = obj_array[-1]
    if len(last_row) != 1:
        return

    # get last row collection
    coll = bpy.data.collections.get(last_row[0])

    # remove the collection if empty
    if coll and not coll.all_objects:
        bpy.data.collections.remove(coll)
        obj_array.pop()


# function generates all vertical, horizontal, and partial lines for a table
def gen_table_lines(context, ts):
    body_coll = bpy.data.collections.get(ts.table_coll)

    # return if table has no objects
    if len(body_coll.all_objects) == 0:
        return

    # generate all vertical lines
    for vline in ts.align.vline_pos:
        for (start_y, end_y) in vline.y_pos:
            line_length_v = end_y - start_y
            gen_line_object(context, ts.init_params, ts.table_coll, vline.x_pos, start_y, line_length_v, 'y')

    # generate vertical lines for multicolumn
    for vline in ts.multi.vline_pos:
        for (start_y, end_y) in vline.y_pos:
            line_length_v = end_y - start_y
            gen_line_object(context, ts.init_params, ts.table_coll, vline.x_pos, start_y, line_length_v, 'y')

    x_pos = ts.init_params.width
    line_length_h = gen_bound(body_coll.name, 'x', 'max') - ts.init_params.width

    # generate all horizontal lines (hline)
    for y_pos in ts.hline.hline_pos:
        gen_line_object(context, ts.init_params, ts.table_coll, x_pos, y_pos, line_length_h)

    max_col = len(ts.align.column_width) - 1

    # generate all partial horizontal lines (cline)
    for y_pos, (start, end) in zip(ts.hline.cline_pos, ts.hline.cline_range):
        # clamp start and end to number of columns
        start = min(start, max_col)
        end = min(end, max_col)

        x_pos = ts.align.column_width[start - 1]
        line_length_c = ts.align.column_width[end] - x_pos

        gen_line_object(context, ts.init_params, ts.table_coll, x_pos, y_pos, line_length_c)
