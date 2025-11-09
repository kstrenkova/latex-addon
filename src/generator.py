# ---------------------------------------------------------------------------
# File name   : generator.py
# Created By  : Katarina Strenkova
# ---------------------------------------------------------------------------

import bpy

from bpy_extras.object_utils import object_data_add  # add sqrt symbol
from ..data.characters_db import unicode_chars_big, LINE_SPACE
from .syntax_utils import change_font

from mathutils import Vector  # vertices


# function generates text in given font
def gen_text(text, font_info, collection):
    text_data = bpy.data.curves.new("Text", type='FONT')
    text_data.body = text

    if font_info != "":
        text_data.font = font_info['font']
        text_data.size = font_info['size']

    # changing size for bigger symbols, e.g. sum, integral
    if text in unicode_chars_big.values():
        text_data.size *= 1.5

    text_obj = bpy.data.objects.new("Text", text_data)
    bpy.data.collections[collection].objects.link(text_obj)
    bpy.context.view_layer.objects.active = text_obj


def gen_set_position(param):
    # save active object
    obj = bpy.context.active_object

    # scale object
    obj.scale.x = param.scale
    obj.scale.y = param.scale

    obj.location.x = param.width  # move by width (x)
    obj.location.y = param.height  # move by height (y)
    obj.location.z = 0.0


def gen_move_position(param):
    # save active object
    obj = bpy.context.active_object
    gen_set_position(param)

    # get corners of bounding box
    bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    obj_dimension = bbox[4].x * param.scale
    param.width += obj_dimension + (0.1 * param.scale)  # space


# function gets object into collection
def gen_into_collection(collection, symbol):
    for obj in bpy.data.collections[collection].objects:
        # object is already in collection
        if obj.name == symbol.name:
            return

    # unlink from all collections
    for coll in symbol.users_collection:
        coll.objects.unlink(symbol)

    # link object into the correct collection
    bpy.data.collections[collection].objects.link(symbol)


# function creates new collection
def gen_new_collection(coll_name, parent_coll):
    # add new collection
    collection = bpy.data.collections.new(coll_name)
    bpy.data.collections[parent_coll].children.link(collection)
    return collection.name


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


# function generates square root symbol
def gen_sqrt_sym(context):
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

    # location of 3D cursor
    cursor_3D = bpy.context.scene.cursor.location

    # set origin for sqrt
    bpy.context.scene.cursor.location += Vector((-0.5266461968421936, -0.8238898515701294, 0.0))
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

    # set 3D cursor back
    bpy.context.scene.cursor.location = cursor_3D

    # recalculate normals in editmode
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.editmode_toggle()


# function moves sqrt symbol according to given parameters
def gen_sqrt_move(context, param, sqrt_param, move):
    # position sqrt
    param.height -= 0.25 * param.scale
    gen_set_position(param)
    param.height += 0.25 * param.scale

    # apply scale
    bpy.ops.object.transform_apply(scale=True, location=False, rotation=False)

    # don't modify square root symbol
    if not move:
        return

    # data of created sqrt symbol
    obj_data = context.active_object.data
    vertices = obj_data.vertices

    # common parameters
    text_height = param.height - (0.2 * param.scale)

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

    line_size_top = 0.05929052829742433 * param.scale  # size of upper line
    move_by_top = sqrt_param['y_max'] - text_height + (0.2 * param.scale)  # y location and space

    # if height of sqrt is not correct
    if (max_y - 0.06) <= move_by_top:
        threshold_top = max_y - (0.06 * param.scale)

        # changing height of sqrt symbol
        for v in vertices:
            if v.co.y == max_y:
                v.co.y = move_by_top + line_size_top
            elif v.co.y >= threshold_top:
                v.co.y = move_by_top

    line_size_bottom = 0.14427322149276733 * param.scale  #  space between lowest points
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


# function generates line for fractions
def gen_frac_line(context, param, x_pos):
    # calculate line height
    line_height = 0.025 * param.scale

    verts = [
        Vector((0.0, -line_height, 0.0)),
        Vector((0.0, line_height, 0.0)),
        Vector((1.0, line_height, 0.0)),
        Vector((1.0, -line_height, 0.0))
    ]
    edges = []
    faces = [[0, 1, 2, 3]]

    mesh = bpy.data.meshes.new(name="Line")
    mesh.from_pydata(verts, edges, faces)
    object_data_add(context, mesh)

    # location of line
    line_obj = context.active_object
    line_obj.location = Vector((
        param.width,
        param.height + 0.3 * param.scale,
        0.0
    ))

    # moving fraction line
    for i in bpy.context.object.data.vertices:
        new_location = i.co
        if i.co.x == 1.0:
            new_location[0] = x_pos - param.width + 0.1 * param.scale  # x position
        i.co = new_location


# function calculates the scaling and height of text
def gen_calculate(param, text_scale, levels):
    # height factors
    first_exp = 0.75
    nested_exp = 0.5
    first_ix = 0.5
    nested_ix = 0.25

    # scale factors
    scale_low = 0.65
    scale_nested = 0.45

    lvl_exp = 0  # exponent lvl
    lvl_ix = 0  # index lvl

    # starting height is line height and scale is user given scale
    param.height = param.line
    param.scale = text_scale

    # iterating through array of exponents and indexes
    for item in levels.ei_array:

        # deciding scaling
        if (lvl_exp + lvl_ix) == 0:
            # depending on fraction level
            param.scale = (scale_low if levels.frac < 2 else scale_nested) * text_scale
        else:
            param.scale = scale_nested * text_scale

        # adding number of exponent or index
        if item == "exp":
            lvl_exp += 1
            factor = first_exp if lvl_exp == 1 else nested_exp
            param.height += factor * param.scale
        else:
            lvl_ix += 1
            factor = first_ix if lvl_ix == 1 else nested_ix
            param.height -= factor * param.scale


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
            obj.location.y += bbox[2].y - min_y + 0.25 * param.scale
        else:
            obj.location.y += bbox[0].y - max_y - 0.25 * param.scale

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
        gen_bound(up_collection, 'x', 'max'),
        gen_bound(down_collection, 'x', 'max'),
        sum_width
    )

    diff = fin_width - sum_width

    # index or exponent is longer than sum symbol
    if diff > 0:
        up_objects = bpy.data.collections[up_collection].all_objects
        down_objects = bpy.data.collections[down_collection].all_objects
        obj_move = [sum_symbol] + list(up_objects) + list(down_objects)
        for obj in obj_move:
            obj.location.x += diff  # move objects

    return fin_width + diff


# function moves objects in fraction
def gen_frac_move(param, collection, mode):
    # get highest or lowest point in collection
    y = gen_bound(collection, 'y', 'max') if mode == "den" else gen_bound(collection, 'y', 'min')
    move_by = param.height - y + (0.1 if mode == "den" else 0.6) * param.scale

    # select and move all objects in denominator
    for obj in bpy.data.collections[collection].all_objects:
        obj.location.y += move_by


# function centers objects on x axis
def gen_center(obj1, obj2, collection):
    # find wider text
    diff = obj1 - obj2 if (obj1 > obj2) else obj2 - obj1
    move_by = diff / 2.0  # space between x positions div 2

    # move all objects
    for obj in bpy.data.collections[collection].all_objects:
        obj.location.x += move_by


# function returns extreme for set axis and type (min/max)
def gen_bound(collection, axis, ftype):
    bpy.ops.object.select_all(action='DESELECT')  # deselect all objects
    objects = bpy.data.collections[collection].all_objects
    if not objects:
        return 0

    # determine which corner index to check
    if axis == 'x' and ftype == 'max':
        corner_index = 4
    elif axis == 'y' and ftype == 'max':
        corner_index = 2
    else:
        corner_index = 0

    func = max if ftype == 'max' else min

    # save position of all objects
    positions = []
    for obj in objects:
        obj.select_set(True)
        bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        positions.append(getattr(bbox[corner_index], axis))

    # return max or min from all positions
    return func(positions)


# function positions matrix figure
def gen_matrix_pos(context, obj_array, param):
    # return if matrix has no objects
    if not len(obj_array):
        return

    # get maximum number of cells in row
    max_cell_x = 0
    for row in obj_array:
        max_cell_x = max(max_cell_x, len(row))

    gen_matrix_x(context, obj_array, param, max_cell_x)  # center by x axis
    gen_matrix_y(obj_array, param, max_cell_x)  # move by y axis


# function centers matrix horizontally
def gen_matrix_x(context, obj_array, param, max_cell_x):
    i = 0  # collumn number

    while i < max_cell_x:
        max_width = 0
        # iterate through rows
        for row in obj_array:
            # getting maximum width in collumn 'i'
            if i >= len(row):
                cell_width = 0
            else:
                collection = row[i]
                cell_width = gen_bound(collection, 'x', 'max')

            max_width = max(max_width, cell_width)

        # iterate through rows
        for row in obj_array:
            # deselect all objects
            bpy.ops.object.select_all(action='DESELECT')

            # move objects in next collumn
            if (i+1) < len(row):
                collection = row[i+1]

                # select objects and find minimum x position
                min_x = gen_bound(collection, 'x', 'min')

            # set x position
            for obj in context.selected_objects:
                old_location = obj.location.x
                obj.location.x = max_width + (old_location - min_x) + 0.5 * param.scale

        # iterate through rows
        for row in obj_array:
            # center objects in row
            if len(row) > i:
                collection = row[i]
                cell_width = gen_bound(collection, 'x', 'max')
                gen_center(cell_width, max_width, collection)

        i += 1  # next collumn


# function moves matrix vertically
def gen_matrix_y(obj_array, param, max_cell_x):
    is_init = False  # set initialisation flag

    # iterate through rows
    for row in obj_array:
        # if the row is not empty
        if len(row):
            # getting maximum height in row
            i = 0  # collumn number
            while i < max_cell_x:
                # first collumn
                if i == 0:
                    collection = row[i]
                    cell_height = gen_bound(collection, 'y', 'max')
                    max_height = cell_height
                # less collumns than maximum
                elif i >= len(row):
                    cell_height = max_height
                else:
                    collection = row[i]
                    cell_height = gen_bound(collection, 'y', 'max')

                max_height = max(max_height, cell_height)
                i += 1  # next cell

            # first iteration
            if not is_init:
                min_height = max_height + 0.1 * param.scale
                is_init = True

            # move row if its highest point cuts into the upper row
            if max_height > (min_height - 0.1 * param.scale):
                i = 0  # collumn number
                while i < max_cell_x:
                    # row is not empty
                    if i < len(row):
                        collection = row[i]
                        move_by = max_height - min_height + 0.5 * param.scale  # space

                        # move objects lower
                        for obj in bpy.data.collections[collection].all_objects:
                            obj.location.y -= move_by

                    i += 1  # next cell

            # getting minimum height in row
            i = 0  # collumn number
            while i < max_cell_x:
                # first collumn
                if i == 0:
                    collection = row[i]
                    cell_height = gen_bound(collection, 'y', 'min')
                    min_height = cell_height
                # less collumns than maximum
                elif i >= len(row):
                    cell_height = min_height
                else:
                    collection = row[i]
                    cell_height = gen_bound(collection, 'y', 'min')

                min_height = min(min_height, cell_height)
                i += 1  # next cell


# TODO vmatrix and Vmatrix have tricky space after left bracket
# function generates matrix brackets
def gen_brackets(context, param, collection, size):
    # determine left or right bracket
    is_left = (size.max_x == -1)
    x = size.min_x if is_left else size.max_x

    bracket = context.active_object

    # scale bracket object
    matrix_height = size.max_y - size.min_y
    scale = (matrix_height + 0.5 * param.scale) / bracket.dimensions.y
    bracket.scale.x = scale / 3.0
    bracket.scale.y = scale

    # force update after scaling
    bpy.context.view_layer.update()

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
def gen_matrix_center(collection, size, y_line):
    # calculate center location
    center_loc = (size.max_y + size.min_y) / 2.0
    offset = center_loc + abs(y_line)

    # center matrix into row
    for obj in bpy.data.collections[collection].all_objects:
        obj.location.y -= offset


def gen_bullet_point(param, defaults, text):
    # TODO scale
    gen_text(text, change_font('base'), defaults.current_coll)
    param.line -= 1.0
    param.height = param.line

    obj = bpy.context.active_object  # save active object

    bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    obj_dimension = bbox[4].x * param.scale
    param.width = (1.3 - obj_dimension) * param.scale  # space before bullet point

    gen_move_position(param)
    param.width += 0.3 * param.scale  # space after bullet point