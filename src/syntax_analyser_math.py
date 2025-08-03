# ---------------------------------------------------------------------------
# File name   : syntex_analyser_math.py
# Created By  : Katarina Strenkova
# ---------------------------------------------------------------------------

import bpy
import os.path

# functions from generator
from .lexical_analyser import LexicalAnalyser
from .generator import *

# TODO get rid of ..data
from ..data.ll_table import *
from ..data.characters_db import *


# class that holds default settings
class Defaults:
    def __init__(self, context, custom_prop, base_coll):
        self.context = context
        self.text_scale = custom_prop.text_scale
        self.font_path = custom_prop.font_path
        self.font = []  # default_font, unicode_font
        self.base_collection = base_coll
        self.current_collection = base_coll


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


# class for levels
class Levels:
    def __init__(self, ei_array, frac):
        self.ei_array = ei_array
        self.frac = frac


# class fot sum
class Sum:
    def __init__(self):
        self.bool = False
        self.name = ''
        self.array = []


# class for index and exponent
class ExpIxState:
    def __init__(self, parent_coll, init_params):
        self.parent_coll = parent_coll
        self.init_params = init_params
        self.eicoll = ''
        self.eicoll2 = ''
        self.width = 0


# class for fraction
class FractionState:
    def __init__(self, parent_coll, init_params):
        self.parent_coll = parent_coll
        self.init_params = init_params
        self.ncoll = ''
        self.dcoll = ''
        self.nwidth = 0
        self.dwidth = 0

# class for square root
class SqrtState:
    def __init__(self, parent_coll, init_params):
        self.parent_coll = parent_coll
        self.init_params = init_params
        self.sqcoll = ''


# class for matrix
class MatrixState:
    def __init__(self, parent_coll, init_params):
        self.parent_coll = parent_coll
        self.init_params = init_params
        self.xy_size = []
        self.mx_coll = ''
        self.obj_array = [[]]
        self.row_num = 0


class MathSyntaxAnalyser(LexicalAnalyser):
    def __init__(self, context, custom_prop, base_coll, pos):
        super().__init__(custom_prop.latex_text, pos)

        self.stack = ['$', 'PROG']
        self.state_stack = []
        self.parsing_context = "DEFAULT"

        self.d = Defaults(context, custom_prop, base_coll)
        self.parameters = Parameters(custom_prop.text_scale, 0.0, 0.0, 0.0)
        self.sum = Sum()
        self.levels = Levels([], 0)
        self.ms_brackets = "matrix"

    def peek_token(self):
        token = self.get_token()
        self.return_token(token)
        return token

    def choose_rule(self, stack_top, token):
        # TODO clean lookup
        # TODO ANGLE_BRACKETS OUTSIDE OF SQRT

        if token.type in {"COMMAND", "CLOSE_BRACKET", "OPEN_BRACKET"}:
            key = token.value
        else:
            key = token.type

        if self.parsing_context == "SQRT" and token.type == "ANGLE_BRACKET" and token.value in {'[', ']'}:
            key = token.value

        elif token.type == "COMMAND" and token.value in unicode_chars and token.value != 'sum':
            key = "_MATH_SYMBOL"

        elif token.type == "_TEXT" and token.value in matrix_brackets:
            self.ms_brackets = token.value
            key = "matrix"

        elif (token.value != '_' and stack_top == 'IX') or \
            (token.value != '^' and stack_top == 'EXP'):
            key = "epsilon"

        if stack_top == "PROG":
            key = "_ANY"

        rule = math_ll_table.get((stack_top, key))
        return rule

    def execute_action(self, action, token):
        # Context actions
        if action == '#ACTION_SQRT_CONTEXT':
            print("Context change: Entering SQRT")
            self.parsing_context = 'SQRT'
            return True

        elif action == '#ACTION_RESET_CONTEXT':
            print(f"Context change: Leaving {self.parsing_context}")
            self.parsing_context = 'DEFAULT'
            return True

        # <CONST> actions
        elif action == '#ACTION_GENERATE_TEXT':
            token = self.get_token()
            gen_text(self.d.context, token.value, self.d.font[0])
            gen_calculate(self.parameters, self.d.text_scale, self.levels)
            gen_position(self.parameters, True)
            print("BASE COLLECTION", self.d.base_collection)
            gen_collection(self.d.current_collection, self.d.base_collection)
            return True

        elif action == '#ACTION_LEVEL_DOWN':
            self.levels.ei_array.append("ix")
            gen_calculate(self.parameters, self.d.text_scale, self.levels)
            return True

        elif action == '#ACTION_LEVEL_UP':
            self.levels.ei_array.append("exp")
            gen_calculate(self.parameters, self.d.text_scale, self.levels)
            return True

        # <COMMAND> actions
        elif action == '#ACTION_SPACE':
            token = self.get_token()
            space = space_sizes[token.value] * self.parameters.scale
            self.parameters.width += space
            return True

        elif action == '#ACTION_INTEGRAL':
            gen_calculate(self.parameters, self.d.text_scale, self.levels)
            gen_position(self.parameters, True)

            # move prod and integral symbol
            self.d.context.active_object.location.y -= 0.3 * self.parameters.scale
            self.parameters.width -= 0.2 * self.parameters.scale
            gen_collection(self.d.current_collection, self.d.base_collection)
            return True

        elif action == '#ACTION_MATH_SYMBOL':
            token = self.get_token()
            if token.value in unicode_chars:
                gen_text(self.d.context, unicode_chars[token.value], self.d.font[1])

            gen_calculate(self.parameters, self.d.text_scale, self.levels)
            gen_position(self.parameters, True)
            gen_collection(self.d.current_collection, self.d.base_collection)
            return True

        # <TERM_EI> actions
        elif action == '#ACTION_EI_INIT':
            token = self.get_token()
            eis = ExpIxState(self.d.current_collection, self.parameters.create_copy())
            eis.width = gen_group_width(self.d.current_collection)

            # exponent or index collection
            coll_name = 'ExponentCollection' if token.type == '_CARET' else 'IndexCollection'
            eicoll = bpy.data.collections.new(coll_name)
            bpy.data.collections[self.d.current_collection].children.link(eicoll)
            eis.eicoll = eicoll.name

            self.state_stack.append(eis)

            self.d.current_collection = eicoll.name
            return True

        elif action == "#ACTION_EI_SINGLE":
            eis = self.state_stack.pop()
            self.levels.ei_array.pop()

            if self.sum.bool:
                gen_move_sum(self.parameters, eis.eicoll, self.sum)
                space = 0.1 * self.parameters.scale
                self.parameters.width = gen_fin_sum(self.d.context, self.sum, eis.eicoll, eis.eicoll) + space

            # join collection into parent collection
            gen_join_collections(eis.eicoll, eis.parent_coll)
            self.d.current_collection = eis.parent_coll  # set current collection
            self.sum.bool = False
            return True

        elif action == '#ACTION_EI_BOTH':
            token = self.get_token()
            self.levels.ei_array.pop()
            eis = self.state_stack[-1]

            if self.sum.bool:
                gen_move_sum(self.parameters, eis.eicoll, self.sum)

            # exponent or index collection
            coll_name = 'ExponentCollection' if token.type == '_CARET' else 'IndexCollection'
            eicoll = bpy.data.collections.new(coll_name)
            bpy.data.collections[eis.parent_coll].children.link(eicoll)
            eis.eicoll2 = eicoll.name

            self.d.current_collection = eicoll.name

            # return width for the second index or exponent
            self.parameters.width = eis.init_params.width
            return True

        elif action == '#ACTION_EI_FINAL':
            eis = self.state_stack.pop()

            # calculate final width
            sec_width = gen_group_width(self.d.current_collection)
            fin_width = max(eis.width, sec_width)

            self.parameters.width = fin_width + 0.1 * self.parameters.scale
            self.levels.ei_array.pop()

            if self.sum.bool:
                gen_move_sum(self.parameters, eis.eicoll2, self.sum)
                space = 0.1 * self.parameters.scale
                self.parameters.width = gen_fin_sum(self.d.context, self.sum, eis.eicoll, eis.eicoll2) + space

            # join collection into parent collection
            gen_join_collections(eis.eicoll, eis.parent_coll)
            gen_join_collections(eis.eicoll2, eis.parent_coll)
            self.d.current_collection = eis.parent_coll  # set current collection
            self.sum.bool = False
            return True

        # <SQRT> actions
        elif action == '#ACTION_SQRT_INIT':
            # saving parameters
            gen_calculate(self.parameters, self.d.text_scale, self.levels)
            sqs = SqrtState(self.d.current_collection, self.parameters.create_copy())

            sqrt_width = 0.855927586555481  # width of square root symbol

            # mode 'single' doesn't have multipliers
            #if mode == "single":
            self.parameters.width += sqrt_width * self.parameters.scale
            # else:
            #     tmp_param.width -= (sqrt_width - 0.4) * self.parameters.scale
            #     self.parameters.width += 0.4 * self.parameters.scale

            # square root collection
            sqcoll = bpy.data.collections.new("SqrtCollection")
            bpy.data.collections[sqs.parent_coll].children.link(sqcoll)
            sqs.sqcoll = sqcoll.name

            self.state_stack.append(sqs)

            self.d.current_collection = sqcoll.name
            return True

        elif action == '#ACTION_SQRT_CREATE':
            sqs = self.state_stack.pop()

            use_param = False
            sqrt_param = {
                "x_pos": 0,
                "y_min": 0,
                "y_max": 0
            }

            # gets parameters of text under square root
            if len(sqs.sqcoll.all_objects):
                use_param = True
                sqrt_param['x_pos'] = gen_group_width(sqs.parent_coll)
                sqrt_param['y_min'] = gen_min_y(sqs.parent_coll)
                sqrt_param['y_max'] = gen_group_height(sqs.parent_coll)

            # generating sqrt symbol
            gen_sqrt_sym(self.d.context)
            gen_collection(sqs.parent_coll, sqs.sqcoll)  # symbol into collection

            # move sqrt symbol
            gen_sqrt_move(self.d.context, sqs.init_params, sqrt_param, use_param)

            # join collection into parent collection
            gen_join_collections(sqs.sqcoll, sqs.parent_coll)
            self.d.current_collection = sqs.parent_coll  # set current collection
            return True

        # <FRAC> actions
        elif action == '#ACTION_FRAC_INIT':
            # increasing level of fraction
            self.levels.frac += 1
            self.parameters.width += 0.1 * self.parameters.scale  # space before fraction

            gen_calculate(self.parameters, self.d.text_scale, self.levels)

            parent_coll = bpy.data.collections[self.d.current_collection]
            fs = FractionState(parent_coll, self.parameters.create_copy())

            # numerator collection
            ncoll = bpy.data.collections.new("NumeratorCollection")
            bpy.data.collections[self.d.current_collection].children.link(ncoll)
            fs.ncoll = ncoll.name

            self.state_stack.append(fs)

            self.d.current_collection = ncoll.name
            return True

        elif action == '#ACTION_FRAC_UP':
            fs = self.state_stack[-1]

            # gets the furthest x position
            if len(bpy.data.collections[self.d.current_collection].all_objects):
                fs.nwidth = gen_group_width(self.d.current_collection)

            # move numerator objects
            gen_calculate(self.parameters, self.d.text_scale, self.levels)
            gen_frac_num(self.parameters, fs.ncoll)

            # denominator collection
            dcoll = bpy.data.collections.new("DenominatorCollection")
            fs.parent_coll.children.link(dcoll)
            fs.dcoll = dcoll.name

            self.d.current_collection = dcoll.name

            # reloading last width
            self.parameters.width = fs.init_params.width
            return True

        elif action == '#ACTION_FRAC_DOWN':
            fs = self.state_stack.pop()

            # gets the furthest x position
            if len(bpy.data.collections[self.d.current_collection].all_objects):
                fs.dwidth = gen_group_width(self.d.current_collection)

            # move denominator objects
            gen_calculate(self.parameters, self.d.text_scale, self.levels)
            gen_frac_den(self.parameters, fs.dcoll)

            # finding longer text width
            if fs.dwidth > fs.nwidth:
                line_length = fs.dwidth
                center_coll = fs.ncoll
            else:
                line_length = fs.nwidth
                center_coll = fs.dcoll

            # generating fraction line
            gen_frac_line(self.d.context, fs.init_params, line_length)

            # center numerator and denominator
            gen_center(fs.nwidth, fs.dwidth, center_coll)
            gen_collection(fs.dcoll, self.d.base_collection)

            # join numerator and denominator collections
            gen_join_collections(fs.dcoll, fs.ncoll)

            # join denominator collection into parent collection
            gen_join_collections(fs.ncoll, fs.parent_coll)
            self.d.current_collection = fs.parent_coll  # set current collection

            # set back line width
            self.parameters.width = line_length + 0.2 * self.parameters.scale  # space

            # decreasing level of fraction
            self.levels.frac -= 1
            return True

        # <SUM> actions
        elif action == '#ACTION_SUM_INIT':
            gen_text(self.d.context, unicode_chars['sum'], self.d.font[1])

            gen_calculate(self.parameters, self.d.text_scale, self.levels)
            self.parameters.height -= 0.4 * self.parameters.scale  # move lower
            gen_position(self.parameters, True)
            gen_collection(self.d.current_collection, self.d.base_collection)

            self.sum.name = self.d.context.active_object.name  # save sum object
            self.sum.bool = True
            return True

        # <MATRIX> actions
        elif action == '#ACTION_MATRIX_INIT':
            gen_calculate(self.parameters, self.d.text_scale, self.levels)

            # saving state of the matrix
            ms = MatrixState(self.d.current_collection, self.parameters.create_copy())
            ms.xy_size.append(ms.init_params.width) # array for matrix parameters

            # matrix collection
            mx_coll = bpy.data.collections.new("MatrixBodyCollection")
            bpy.data.collections[self.d.current_collection].children.link(mx_coll)
            ms.mx_coll = mx_coll.name

            self.state_stack.append(ms)

            # first matrix cell collection
            self.d.current_collection = gen_new_collection("MatrixCellCollection", mx_coll)
            ms.obj_array[ms.row_num].append(self.d.current_collection)
            return True

        elif action == '#ACTION_MATRIX_NEW_ROW':
            token = self.get_token()
            ms = self.state_stack[-1]

            # matrix cell collection
            self.d.current_collection = gen_new_collection("MatrixCellCollection", ms.parent_coll)

            # add new array that represents row
            ms.obj_array.append([])
            ms.row_num += 1
            ms.obj_array[ms.row_num].append(self.d.current_collection)

            # set width to start and height lower
            self.parameters.width = ms.init_params.width
            self.parameters.line -= 1.0 * self.d.text_scale
            return True

        elif action == '#ACTION_MATRIX_NEW_CELL':
            token = self.get_token()
            ms = self.state_stack[-1]

            # matrix cell collection
            self.d.current_collection = gen_new_collection("MatrixCellCollection", ms.parent_coll)

            # add collection to row
            ms.obj_array[ms.row_num].append(self.d.current_collection)
            return True

        elif action == '#ACTION_MATRIX_CREATE':
            ms = self.state_stack.pop()

            # position matrix
            gen_matrix_pos(self.d.context, ms.obj_array, self.parameters)

            # get matrix parameters
            ms.xy_size = gen_matrix_param(True, ms.parent_coll, ms.xy_size)
            bracket_type = matrix_brackets[self.ms_brackets]

            if not self.ms_brackets == 'matrix':
                # generate left bracket of matrix
                gen_text(self.d.context, bracket_type[0], self.d.font[1])
                gen_brackets(self.d.context, self.parameters, ms.parent_coll, self.d.base_collection, ms.xy_size, True)
                ms.xy_size = gen_matrix_param(False, ms.parent_coll, ms.xy_size)

                # generate right bracket of matrix
                gen_text(self.d.context, bracket_type[1], self.d.font[1])
                gen_brackets(self.d.context, self.parameters, ms.parent_coll, self.d.base_collection, ms.xy_size, False)

            # center matrix into row
            gen_matrix_center(self.parameters, ms.parent_coll, ms.xy_size)

            # set width of parameters
            self.parameters.width = gen_group_width(ms.mx_coll) + 0.25

            # link objects to matrix collection
            for collection in bpy.data.collections:
                if "MatrixCellCollection" in collection.name:
                    # join all objects into one parent collection
                    for obj in collection.all_objects:
                        bpy.data.collections[ms.mx_coll].objects.link(obj)
                        collection.objects.unlink(obj)

                    # remove matrix cell collection
                    bpy.data.collections.remove(collection)

            # join matrix collection into parent collection
            gen_join_collections(ms.mx_coll, ms.parent_coll)
            self.d.current_collection = ms.parent_coll  # set current collection
            return True

        else:
            print(f"Unknown action: '{action}'")
            return False

    # main function for parsing process
    def parse(self):
        try:
            # chosen default font
            if self.d.font_path != "":
                self.d.font.append(bpy.data.fonts.load(self.d.font_path))

            # unicode font for mathematical symbols
            src_dir = os.path.dirname(__file__)
            font_file = os.path.join(os.path.dirname(src_dir), "data", "fonts", "Kelvinch-Roman.otf")
            self.d.font.append(bpy.data.fonts.load(font_file))

        except Exception as e:
            print(f"Error during initialization: {e}")
            return False, 0

        # parsing loop
        while self.stack:
            stack_top = self.stack[-1]
            token = self.peek_token()
            print(f"STACK: {self.stack}")

            # TODO MATH MODE END
            if stack_top == '$' and token.value == '$' and token.type == '_DOLLAR_SIGN':
                pos = self.get_position()
                print("Position:", pos)
                return True, pos

            # actions
            elif stack_top.startswith('#'):
                action = self.stack.pop()
                print(f"CT {token.value}")
                if not self.execute_action(action, token):
                    print(f"Action error: {action}")
                    return False, 0

            # terminal
            elif not (stack_top.isupper() and stack_top != '$'):
                if stack_top == token.value:
                    self.stack.pop()
                    self.get_token()
                else:
                    print(f"Syntax Error: Expected '{stack_top}' but got '{token.value}'")
                    return False, 0

            # non-terminal
            else:
                print(f"Token type: '{token.type}'")
                print(f"Token value: '{token.value}'")
                rule = self.choose_rule(stack_top, token)

                if rule:
                    self.stack.pop()
                    if rule != ['epsilon']:
                        for symbol in reversed(rule):
                            self.stack.append(symbol)
                else:
                    print(f"Syntax Error: No rule for ({stack_top}, {token.type}, {token.value})")
                    return False, 0

        if self.stack:
            print("Error, not all tokens have been read!")
            return False, 0
