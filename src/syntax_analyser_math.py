# ---------------------------------------------------------------------------
# File name   : syntex_analyser_math.py
# Created By  : Katarina Strenkova
# ---------------------------------------------------------------------------

import bpy

from .generator import *
from .syntax_utils import change_font

# TODO get rid of ..data
from ..data.ll_table import *
from ..data.characters_db import *


# class for levels
class Levels:
    def __init__(self):
        self.ei_array = []
        self.frac = 0
        self.sqrt = False
        self.sym_name = ''


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
        self.size = MatrixSize()
        self.mx_coll = ''
        self.cell_colls = []
        self.obj_array = [[]]
        self.row_num = 0
        self.brackets = 'matrix'


# class for matrix dimensions
class MatrixSize:
    def __init__(self):
        self.min_x = -1
        self.min_y = -1
        self.max_x = -1
        self.max_y = -1
        self.bracket_width = -1


class MathSyntaxAnalyser:
    def __init__(self, lex, defaults, parameters):
        self.stack = ['$', 'PROG']
        self.state_stack = []

        self.lex = lex
        self.d = defaults
        self.parameters = parameters
        self.levels = Levels()

    def math_mode_end(self, stack_top, token):
        if stack_top != '$':
            return False

        return (token.type, token.value) in end_tokens

    def choose_rule(self, stack_top, token):
        # TODO clean lookup
        key = token.value if (token.type in special_token_type) else token.type

        if stack_top in epsilon_rules and epsilon_rules[stack_top] != (token.type, token.value):
            key = 'epsilon'

        if stack_top == 'PROG':
            key = '_ANY'

        # special rule for sqrt index context
        if self.levels.sqrt and token.value == ']':
            self.levels.sqrt = False
            return ['epsilon']

        rule = math_ll_table.get((stack_top, key))
        return rule

    def execute_action(self, action):
        # <CONST> actions
        if action == '#ACTION_GENERATE_TEXT':
            token = self.lex.get_token()
            gen_text(token.value, change_font(self.d.user_font), self.d.current_coll)
            gen_calculate(self.parameters, self.d.text_scale, self.levels)
            gen_move_position(self.parameters)
            return True

        elif action == '#ACTION_LEVEL_DOWN':
            self.levels.ei_array.append('ix')
            gen_calculate(self.parameters, self.d.text_scale, self.levels)
            return True

        elif action == '#ACTION_LEVEL_UP':
            self.levels.ei_array.append('exp')
            gen_calculate(self.parameters, self.d.text_scale, self.levels)
            return True

        # <COMMAND> actions
        elif action == '#ACTION_SPACE':
            token = self.lex.get_token()
            space = space_sizes[token.value] * self.parameters.scale
            self.parameters.width += space
            return True

        elif action == '#ACTION_MATH_SYMBOL':
            token = self.lex.get_token()
            if token.value in unicode_chars:
                gen_text(unicode_chars[token.value], change_font('math'), self.d.current_coll)

            gen_calculate(self.parameters, self.d.text_scale, self.levels)
            gen_move_position(self.parameters)
            return True

        # <MATH_FONT>
        elif action.startswith('#ACTION_MATH_FONT'):
            mfont = action.removeprefix('#ACTION_MATH_FONT_').lower()
            self.state_stack.append(mfont)
            return True

        elif action == '#ACTION_REMOVE_MATH_FONT':
            self.state_stack.pop()
            return True

        elif action == '#ACTION_GENERATE_MATH_LETTER':
            token = self.lex.get_token()
            mfont = self.state_stack[-1]

            # divide token into letters
            for letter in token.value:
                # only supports uppercase letters
                if letter.isupper():
                    gen_text(unicode_fonts[mfont][letter], change_font('math'), self.d.current_coll)
                    gen_calculate(self.parameters, self.d.text_scale, self.levels)
                    gen_move_position(self.parameters)
                else:
                    print("Function", mfont, "doesn't support the letter", letter, "!")
                    return False

            return True

        # <TERM_EI> actions
        elif action == '#ACTION_EI_INIT':
            token = self.lex.get_token()
            eis = ExpIxState(self.d.current_coll, self.parameters.create_copy())
            eis.width = gen_bound(self.d.current_coll, 'x', 'max')

            # exponent or index collection
            coll_name = 'ExponentCollection' if token.type == '_CARET' else 'IndexCollection'
            eis.eicoll = gen_new_collection(coll_name, eis.parent_coll)
            self.d.current_coll = eis.eicoll

            self.state_stack.append(eis)
            return True

        elif action == '#ACTION_EI_SINGLE':
            eis = self.state_stack.pop()
            self.levels.ei_array.pop()

            # move range operator symbol (sum, int, ...) if present
            if self.levels.sym_name != '':
                gen_move_sum(self.parameters, eis.eicoll, self.levels.sym_name)
                space = MIN_SPACE * self.parameters.scale
                self.parameters.width = gen_fin_sum(self.levels.sym_name, eis.eicoll, eis.eicoll) + space

            # join collection into parent collection
            gen_join_collections(eis.eicoll, eis.parent_coll)
            self.d.current_coll = eis.parent_coll
            self.levels.sym_name = ''
            return True

        elif action == '#ACTION_EI_BOTH':
            token = self.lex.get_token()
            self.levels.ei_array.pop()
            eis = self.state_stack[-1]

            # move range operator symbol (sum, int, ...) if present
            if self.levels.sym_name != '':
                gen_move_sum(self.parameters, eis.eicoll, self.levels.sym_name)

            # exponent or index collection
            coll_name = 'ExponentCollection' if token.type == '_CARET' else 'IndexCollection'
            eis.eicoll2 = gen_new_collection(coll_name, eis.parent_coll)
            self.d.current_coll = eis.eicoll2

            # return width for the second index or exponent
            self.parameters.width = eis.init_params.width
            return True

        elif action == '#ACTION_EI_FINAL':
            eis = self.state_stack.pop()

            # calculate final width
            fin_width = max(eis.width, gen_bound(eis.parent_coll, 'x', 'max'))

            self.parameters.width = fin_width + MIN_SPACE * self.parameters.scale
            self.levels.ei_array.pop()

            # move range operator symbol (sum, int, ...) if present
            if self.levels.sym_name != '':
                gen_move_sum(self.parameters, eis.eicoll2, self.levels.sym_name)
                space = MIN_SPACE * self.parameters.scale
                self.parameters.width = gen_fin_sum(self.levels.sym_name, eis.eicoll, eis.eicoll2) + space

            # join collection into parent collection
            gen_join_collections(eis.eicoll, eis.parent_coll)
            gen_join_collections(eis.eicoll2, eis.parent_coll)
            self.d.current_coll = eis.parent_coll  # set current collection
            self.levels.sym_name = ''
            return True

        # <SQRT> actions
        elif action == ('#ACTION_SQRT_INDEX_BEGIN'):
            self.levels.ei_array.append('exp')
            self.levels.sqrt = True
            gen_calculate(self.parameters, self.d.text_scale, self.levels)
            return True

        elif action.startswith('#ACTION_SQRT_INIT'):
            with_index = len(action.removeprefix('#ACTION_SQRT_INIT'))

            if with_index:
                self.levels.ei_array.pop()
                self.parameters.width += MIN_SPACE  # space before index

            # saving parameters
            gen_calculate(self.parameters, self.d.text_scale, self.levels)
            sqs = SqrtState(self.d.current_coll, self.parameters.create_copy())

            if with_index:
                sqs.init_params.width -= (SQRT_WIDTH - 0.4) * self.parameters.scale
                self.parameters.width += 0.4 * self.parameters.scale
            else:
                self.parameters.width += SQRT_WIDTH * self.parameters.scale

            # square root collection
            sqs.sqcoll = gen_new_collection("SqrtCollection", sqs.parent_coll)
            self.d.current_coll = sqs.sqcoll

            self.state_stack.append(sqs)
            return True

        elif action == '#ACTION_SQRT_CREATE':
            sqs = self.state_stack.pop()

            use_param = False
            sqrt_param = {
                'x_pos': 0,
                'y_min': 0,
                'y_max': 0
            }

            # gets parameters of text under square root
            sq_coll_obj = bpy.data.collections.get(sqs.sqcoll)
            if len(sq_coll_obj.all_objects):
                use_param = True
                sqrt_param['x_pos'] = gen_bound(sqs.sqcoll, 'x', 'max')
                sqrt_param['y_min'] = gen_bound(sqs.sqcoll, 'y', 'min')
                sqrt_param['y_max'] = gen_bound(sqs.sqcoll, 'y', 'max')

            # generating sqrt symbol
            gen_sqrt_sym(self.d.context)
            gen_into_collection(sqs.parent_coll, bpy.context.active_object)

            # move sqrt symbol
            gen_sqrt_move(self.d.context, sqs.init_params, sqrt_param, use_param)

            # join collection into parent collection
            gen_join_collections(sqs.sqcoll, sqs.parent_coll)
            self.d.current_coll = sqs.parent_coll  # set current collection
            return True

        # <FRAC> actions
        elif action == '#ACTION_FRAC_INIT':
            # increasing level of fraction
            self.levels.frac += 1
            self.parameters.width += MIN_SPACE * self.parameters.scale  # space before fraction
            gen_calculate(self.parameters, self.d.text_scale, self.levels)

            fs = FractionState(self.d.current_coll, self.parameters.create_copy())

            # numerator collection
            fs.ncoll = gen_new_collection("NumeratorCollection", fs.parent_coll)
            self.d.current_coll = fs.ncoll

            self.state_stack.append(fs)
            return True

        elif action == '#ACTION_FRAC_UP':
            fs = self.state_stack[-1]

            # gets the furthest x position
            if len(bpy.data.collections[self.d.current_coll].all_objects):
                fs.nwidth = gen_bound(self.d.current_coll, 'x', 'max')

            # move numerator objects
            gen_calculate(self.parameters, self.d.text_scale, self.levels)
            gen_frac_move(self.parameters, fs.ncoll, 'num')

            # denominator collection
            fs.dcoll = gen_new_collection("DenominatorCollection", fs.parent_coll)
            self.d.current_coll = fs.dcoll

            # reloading last width
            self.parameters.width = fs.init_params.width
            return True

        elif action == '#ACTION_FRAC_DOWN':
            fs = self.state_stack.pop()

            # gets the furthest x position
            if len(bpy.data.collections[self.d.current_coll].all_objects):
                fs.dwidth = gen_bound(self.d.current_coll, 'x', 'max')

            # move denominator objects
            gen_calculate(self.parameters, self.d.text_scale, self.levels)
            gen_frac_move(self.parameters, fs.dcoll, 'den')

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
            gen_into_collection(fs.dcoll, bpy.context.active_object)

            # join numerator and denominator collections
            gen_join_collections(fs.dcoll, fs.ncoll)

            # join denominator collection into parent collection
            gen_join_collections(fs.ncoll, fs.parent_coll)
            self.d.current_coll = fs.parent_coll

            # set back line width
            self.parameters.width = line_length + 0.2 * self.parameters.scale  # space

            # decreasing level of fraction
            self.levels.frac -= 1
            return True

        # <RANGE_OP> functions
        elif action == '#ACTION_RANGE_OP_INIT':
            token = self.lex.get_token()
            c = token.value if token.value not in unicode_chars_big else unicode_chars_big[token.value]
            gen_text(c, change_font('math'), self.d.current_coll)

            gen_calculate(self.parameters, self.d.text_scale, self.levels)
            if token.value != 'lim':
                # TODO sum, prod was 0.4
                self.parameters.height -= BASE_SPACE * self.parameters.scale  # move lower
            gen_move_position(self.parameters)
            gen_into_collection(self.d.current_coll, bpy.context.active_object)

            # check if the next token is for creating exponent or index
            ntoken = self.lex.peek_token()
            if (ntoken.type == '_UNDERSCORE' or ntoken.type == '_CARET') and token.value != 'int':
                self.levels.sym_name = self.d.context.active_object.name  # save symbol
            return True

        # <MATRIX> actions
        elif action == '#ACTION_MATRIX_VERIFY_BEGIN':
            token = self.lex.get_token()
            if token.type == '_TEXT' and token.value in matrix_brackets:
                ms = MatrixState(self.d.current_coll, self.parameters.create_copy())
                ms.brackets = token.value
                self.state_stack.append(ms)
                return True

            print("Matrix type", token.value, "is not correct!")
            return False

        elif action == '#ACTION_MATRIX_VERIFY_END':
            token = self.lex.get_token()
            ms = self.state_stack[-1]
            if token.type == '_TEXT' and token.value == ms.brackets:
                self.state_stack.pop()
                return True

            print("Matrix type in begin", ms.brackets, "doesn't match the value in end", token.value)
            return False

        elif action == '#ACTION_MATRIX_INIT':
            gen_calculate(self.parameters, self.d.text_scale, self.levels)

            # saving starting state of the matrix
            ms = self.state_stack[-1]
            ms.size.min_x = ms.init_params.width

            # matrix body collection
            ms.mx_coll = gen_new_collection("MatrixBodyCollection", ms.parent_coll)

            # first matrix cell collection
            self.d.current_coll = gen_new_collection("MatrixCellCollection", ms.mx_coll)
            ms.cell_colls.append(self.d.current_coll)
            ms.obj_array[ms.row_num].append(self.d.current_coll)
            return True

        elif action == '#ACTION_MATRIX_NEW_ROW':
            token = self.lex.get_token()
            ms = self.state_stack[-1]

            # matrix cell collection
            self.d.current_coll = gen_new_collection("MatrixCellCollection", ms.mx_coll)
            ms.cell_colls.append(self.d.current_coll)

            # add new array that represents row
            ms.obj_array.append([])
            ms.row_num += 1
            ms.obj_array[ms.row_num].append(self.d.current_coll)

            # set width to start and height lower
            self.parameters.width = ms.init_params.width
            self.parameters.line -= 1.0 * self.d.text_scale
            return True

        elif action == '#ACTION_MATRIX_NEW_CELL':
            token = self.lex.get_token()
            ms = self.state_stack[-1]

            # matrix cell collection
            self.d.current_coll = gen_new_collection("MatrixCellCollection", ms.mx_coll)
            ms.cell_colls.append(self.d.current_coll)

            # add collection to row
            ms.obj_array[ms.row_num].append(self.d.current_coll)
            return True

        elif action == '#ACTION_MATRIX_CREATE':
            ms = self.state_stack[-1]

            # position matrix
            gen_matrix_pos(self.d.context, ms.obj_array, self.parameters)

            # calculate matrix height
            ms.size.min_y = gen_bound(ms.parent_coll, 'y', 'min')
            ms.size.max_y = gen_bound(ms.parent_coll, 'y', 'max')
            bracket_type = matrix_brackets[ms.brackets]

            if not ms.brackets == 'matrix':
                # generate left bracket of matrix
                gen_text(bracket_type[0], change_font('math'), ms.mx_coll)
                gen_brackets(self.d.context, self.parameters, ms.parent_coll, ms.size)

                # calculate furthest x position
                ms.size.max_x = gen_bound(ms.parent_coll, 'x', 'max')
                ms.size.max_x += ms.size.bracket_width - ms.size.min_x

                # generate right bracket of matrix
                gen_text(bracket_type[1], change_font('math'), ms.mx_coll)
                gen_brackets(self.d.context, self.parameters, ms.parent_coll, ms.size)

            # center matrix into row
            gen_matrix_center(self.parameters, ms.parent_coll, ms.size)

            # set new width and old line
            self.parameters.width = gen_bound(ms.mx_coll, 'x', 'max') + 0.25 * self.d.text_scale
            self.parameters.line = ms.init_params.line

            # link objects to matrix collection
            body_coll = bpy.data.collections.get(ms.mx_coll)
            for coll_name in ms.cell_colls:
                coll = bpy.data.collections.get(coll_name)
                if coll is None:
                    continue

                # join all objects into one parent collection
                for obj in list(coll.objects):
                    body_coll.objects.link(obj)
                    coll.objects.unlink(obj)

                # remove matrix cell collection
                bpy.data.collections.remove(coll)

            # join matrix collection into parent collection
            gen_join_collections(ms.mx_coll, ms.parent_coll)
            self.d.current_coll = ms.parent_coll  # set current collection
            return True

        else:
            print(f"Unknown action: '{action}'")
            return False

    # main function for parsing process
    def parse(self):
        # parsing loop
        while self.stack:
            stack_top = self.stack[-1]
            token = self.lex.peek_token()
            print(f"[M] STACK: {self.stack}")
            print(f"[M] Token type: '{token.type}'")
            print(f"[M] Token value: '{token.value}'")

            if self.math_mode_end(stack_top, token):
                # recalculate position before changing modes
                gen_calculate(self.parameters, self.d.text_scale, self.levels)
                return True

            # actions
            elif stack_top.startswith('#'):
                action = self.stack.pop()
                if not self.execute_action(action):
                    print(f"Action error: {action}")
                    return False

            # terminal
            elif not stack_top.isupper():
                if stack_top == token.value:
                    self.stack.pop()
                    self.lex.get_token()
                else:
                    print(f"Syntax Error: Expected '{stack_top}' but got '{token.value}'")
                    return False

            # non-terminal
            else:
                rule = self.choose_rule(stack_top, token)

                if rule:
                    self.stack.pop()
                    if rule != ['epsilon']:
                        for symbol in reversed(rule):
                            self.stack.append(symbol)
                else:
                    print(f"Syntax Error: No rule for ({stack_top}, {token.type}, {token.value})")
                    return False

        if self.stack:
            print("Error, not all tokens have been read!")
            return False
