# ---------------------------------------------------------------------------
# File name   : syntex_analyser_math.py
# Created By  : Katarina Strenkova
# ---------------------------------------------------------------------------

import bpy

from .generator import *
from .syntax_utils import (
    Levels,
    ExpIxState,
    FractionState,
    SqrtState,
    MatrixState
)

from .data.ll_table import *
from .data.characters_db import *

# TODO [feature] Add numbers for equation lines
# TODO [optimalization] Go from using collections to python arrays or dictionaries


class MathSyntaxAnalyser:
    def __init__(self, lex, defaults, parameters):
        self.stack = ['$$$', 'PROG']
        self.state_stack = []

        self.lex = lex
        self.d = defaults
        self.p = parameters

        # set default fraction level based on math mode type
        frac_array = [] if self.d.math_mode == 'display' else ['frac']
        self.levels = Levels(frac_array)

    def math_mode_end(self, stack_top, token):
        if stack_top != '$$$':
            return False

        return (token.type, token.value) in end_tokens

    def choose_rule(self, stack_top, token):
        key = token.value if token.type == 'COMMAND' else token.type

        # special epsilon rules
        if stack_top in epsilon_rules and (token.type, token.value) not in epsilon_rules[stack_top]:
            key = 'epsilon'

        if stack_top == 'PROG':
            key = '_ANY'

        # special rule for sqrt index context
        if token.value == ']' and self.levels.sqrt:
            self.levels.sqrt = False
            return ['epsilon']

        rule = math_ll_table.get((stack_top, key))
        return rule

    def execute_action(self, action):
        # <CONST> actions
        if action == '#ACTION_GENERATE_TEXT':
            token = self.lex.get_token()
            gen_text_object(self.p, self.d, token.value, self.d.user_font, self.levels)
            return True

        # new line (\\)
        elif action == '#ACTION_NEW_LINE':
            gen_adjust_new_line(self.p, self.d.base_coll, self.d.line_height)
            return True

        elif action == '#ACTION_LEVEL_DOWN':
            self.levels.ei_array.append('ix')
            gen_calculate(self.p, self.d.text_scale, self.levels)
            return True

        elif action == '#ACTION_LEVEL_UP':
            self.levels.ei_array.append('exp')
            gen_calculate(self.p, self.d.text_scale, self.levels)
            return True

        # <COMMAND> actions
        elif action == '#ACTION_SPACE':
            token = self.lex.get_token()
            space = space_sizes[token.value] * self.p.scale
            self.p.width += space
            return True

        elif action == '#ACTION_MATH_SYMBOL':
            token = self.lex.get_token()
            if not token.value in unicode_chars:
                err = f"Symbol '{token.value}' is not supported."
                print("Syntax error:", err)
                return False

            gen_text_object(self.p, self.d, unicode_chars[token.value], 'math', self.levels)
            return True

        # <MATH_FONT>
        # TODO [feature] Add mathfonts not used only on upper letters
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
                if not letter.isupper():
                    err = f"Function '{mfont}' doesn't support the letter '{letter}'!"
                    print("Syntax error:", err)
                    return False

                # generate math letter
                gen_text_object(self.p, self.d, unicode_fonts[mfont][letter], 'math', self.levels)

            return True

        # <TERM_EI> actions
        elif action == '#ACTION_EI_INIT':
            token = self.lex.get_token()
            eis = ExpIxState(self.d.current_coll, self.p.create_copy(), self.levels.sym_name)
            eis.width = gen_bound(self.d.current_coll, 'x', 'max') or 0.0
            self.levels.sym_name = ''

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
            if eis.sym_name != '' and self.d.math_mode == 'display':
                gen_move_sum(self.p, eis.eicoll, eis.sym_name)
                space = BASE_SPACE * self.p.scale
                self.p.width = gen_fin_sum(eis.sym_name, eis.eicoll, eis.eicoll) + space

            # join collection into parent collection
            gen_join_collections(eis.eicoll, eis.parent_coll)
            self.d.current_coll = eis.parent_coll

            # reset levels
            gen_calculate(self.p, self.d.text_scale, self.levels)
            return True

        elif action == '#ACTION_EI_BOTH':
            token = self.lex.get_token()
            self.levels.ei_array.pop()
            eis = self.state_stack[-1]

            # move range operator symbol (sum, int, ...) if present
            if eis.sym_name != '' and self.d.math_mode == 'display':
                gen_move_sum(self.p, eis.eicoll, eis.sym_name)

            # exponent or index collection
            coll_name = 'ExponentCollection' if token.type == '_CARET' else 'IndexCollection'
            eis.eicoll2 = gen_new_collection(coll_name, eis.parent_coll)
            self.d.current_coll = eis.eicoll2

            # return width for the second index or exponent
            self.p.width = eis.init_params.width
            return True

        elif action == '#ACTION_EI_FINAL':
            eis = self.state_stack.pop()

            # calculate final width
            fin_width = max(eis.width, gen_bound(eis.parent_coll, 'x', 'max') or 0.0)

            self.p.width = fin_width + MIN_SPACE * self.p.scale
            self.levels.ei_array.pop()

            # move range operator symbol (sum, int, ...) if present
            if eis.sym_name != '' and self.d.math_mode == 'display':
                gen_move_sum(self.p, eis.eicoll2, eis.sym_name)
                space = BASE_SPACE * self.p.scale
                self.p.width = gen_fin_sum(eis.sym_name, eis.eicoll, eis.eicoll2) + space

            # join collection into parent collection
            gen_join_collections(eis.eicoll, eis.parent_coll)
            gen_join_collections(eis.eicoll2, eis.parent_coll)
            self.d.current_coll = eis.parent_coll  # set current collection

            # reset levels
            gen_calculate(self.p, self.d.text_scale, self.levels)
            return True

        # <SQRT> actions
        elif action == ('#ACTION_SQRT_INDEX_BEGIN'):
            self.levels.ei_array.append('exp')
            self.levels.sqrt = True
            gen_calculate(self.p, self.d.text_scale, self.levels)
            return True

        elif action.startswith('#ACTION_SQRT_INIT'):
            with_index = len(action.removeprefix('#ACTION_SQRT_INIT'))

            if with_index:
                self.levels.ei_array.pop()
                self.p.width += MIN_SPACE  # space before index

            # saving parameters
            gen_calculate(self.p, self.d.text_scale, self.levels)
            sqs = SqrtState(self.d.current_coll, self.p.create_copy())

            if with_index:
                sqs.init_params.width -= (SQRT_WIDTH - 0.4) * self.p.scale
                self.p.width += 0.4 * self.p.scale
            else:
                self.p.width += SQRT_WIDTH * self.p.scale

            # square root collection
            sqs.sqcoll = gen_new_collection("SqrtCollection", sqs.parent_coll)
            self.d.current_coll = sqs.sqcoll

            self.state_stack.append(sqs)
            return True

        elif action == '#ACTION_SQRT_CREATE':
            sqs = self.state_stack.pop()
            sqrt_param = None

            # gets parameters of text under square root
            sq_coll_obj = bpy.data.collections.get(sqs.sqcoll)
            if sq_coll_obj.all_objects:
                x_pos = gen_bound(sqs.sqcoll, 'x', 'max')
                min_y, max_y = gen_bound_both(sqs.sqcoll, 'y')

                sqrt_param = {
                    'x_pos': x_pos,
                    'y_min': min_y,
                    'y_max': max_y
                }

            # generating sqrt symbol
            sqrt_obj = gen_sqrt_sym(self.d.context, sqs.parent_coll)
            self.p.line.line_objs.append(sqrt_obj)

            # move sqrt symbol
            gen_sqrt_move(sqrt_obj, sqs.init_params, sqrt_param)

            # join collection into parent collection
            gen_join_collections(sqs.sqcoll, sqs.parent_coll)
            self.d.current_coll = sqs.parent_coll  # set current collection
            return True

        # <FRAC> actions
        elif action.startswith('#ACTION_FRAC_SAVE_'):
            item = action.removeprefix('#ACTION_FRAC_SAVE_').lower()
            self.levels.frac_array.append(item)
            return True

        # TODO [fix] Improve visual quality of \dfrac command in every scenario
        elif action == '#ACTION_FRAC_INIT':
            self.p.width += MIN_SPACE * self.p.scale  # space before fraction
            fs = FractionState(self.d.current_coll, self.p.create_copy())

            # numerator collection
            fs.ncoll = gen_new_collection("NumeratorCollection", fs.parent_coll)
            self.d.current_coll = fs.ncoll

            self.state_stack.append(fs)
            return True

        elif action == '#ACTION_FRAC_UP':
            fs = self.state_stack[-1]

            # gets the furthest x position
            fs.nwidth = gen_bound(self.d.current_coll, 'x', 'max') or 0.0

            # move numerator objects
            gen_calculate(self.p, self.d.text_scale, self.levels)
            gen_frac_move(self.p, fs.ncoll, 'num')

            # denominator collection
            fs.dcoll = gen_new_collection("DenominatorCollection", fs.parent_coll)
            self.d.current_coll = fs.dcoll

            # reloading last width
            self.p.width = fs.init_params.width
            return True

        elif action == '#ACTION_FRAC_DOWN':
            fs = self.state_stack.pop()

            # gets the furthest x position
            fs.dwidth = gen_bound(self.d.current_coll, 'x', 'max') or 0.0

            # move denominator objects
            gen_calculate(self.p, self.d.text_scale, self.levels)
            gen_frac_move(self.p, fs.dcoll, 'den')

            # finding longer text width
            if fs.dwidth > fs.nwidth:
                line_length = fs.dwidth
                center_coll = fs.ncoll
            else:
                line_length = fs.nwidth
                center_coll = fs.dcoll

            # center numerator and denominator
            gen_center(fs.nwidth, fs.dwidth, center_coll)

            # generate fraction line
            gen_frac_line(self.d.context, fs.init_params, self.d.current_coll, line_length)
            self.p.line.line_objs.append(self.d.context.active_object)

            # join numerator and denominator collections
            gen_join_collections(fs.dcoll, fs.ncoll)

            # join denominator collection into parent collection
            gen_join_collections(fs.ncoll, fs.parent_coll)
            self.d.current_coll = fs.parent_coll

            # set back line width
            self.p.width = line_length + BASE_SPACE * self.p.scale  # space

            # decreasing level of fraction
            self.levels.frac_array.pop()
            return True

        # <RANGE_OP> functions
        elif action == '#ACTION_SAVE_RANGE_OP':
            self.levels.sym_name = self.d.context.active_object.name
            return True

        elif action == '#ACTION_RANGE_OP_INIT':
            token = self.lex.get_token()
            c = token.value if token.value not in unicode_chars_big else unicode_chars_big[token.value]

            # generate big symbols
            gen_text_object(self.p, self.d, c, 'math', self.levels, token.value)
            return True

        # <MATRIX> actions
        elif action == '#ACTION_MATRIX_VERIFY_BEGIN':
            token = self.lex.get_token()
            if token.type == '_TEXT' and token.value in matrix_brackets:
                ms = MatrixState(self.d.current_coll, self.p.create_copy())
                ms.brackets = token.value
                self.state_stack.append(ms)
                return True

            err = f"Matrix type '{token.value}' is incorrect!"
            print("Syntax error:", err)
            return False

        elif action == '#ACTION_MATRIX_VERIFY_END':
            token = self.lex.get_token()
            ms = self.state_stack[-1]
            if token.type == '_TEXT' and token.value == ms.brackets:
                self.state_stack.pop()
                return True

            err = f"Matrix type in begin '{ms.brackets}' doesn't match the value in end '{token.value}'"
            print("Syntax error:", err)
            return False

        elif action == '#ACTION_MATRIX_INIT':
            gen_calculate(self.p, self.d.text_scale, self.levels)

            # saving starting state of the matrix
            ms = self.state_stack[-1]
            ms.size.min_x = ms.init_params.width

            # matrix body collection
            ms.mx_coll = gen_new_collection("MatrixBodyCollection", ms.parent_coll)

            # first matrix cell collection
            self.d.current_coll = gen_new_collection("MatrixCellCollection", ms.mx_coll)
            ms.obj_array[ms.get_row_num()].append(self.d.current_coll)
            return True

        elif action == '#ACTION_MATRIX_NEW_ROW':
            ms = self.state_stack[-1]

            # add new array that represents row
            ms.obj_array.append([])
            self.execute_action('#ACTION_MATRIX_NEW_CELL')

            # set width to start and height lower
            self.p.width = ms.init_params.width
            self.p.height -= self.d.line_height * self.d.text_scale
            return True

        elif action == '#ACTION_MATRIX_NEW_CELL':
            ms = self.state_stack[-1]

            # matrix cell collection
            self.d.current_coll = gen_new_collection("MatrixCellCollection", ms.mx_coll)

            # add collection to row
            ms.obj_array[ms.get_row_num()].append(self.d.current_coll)
            return True

        elif action == '#ACTION_MATRIX_CREATE':
            ms = self.state_stack[-1]
            self.d.current_coll = ms.mx_coll
            gen_cleanup_last_row(ms.obj_array)

            # position matrix if not empty
            if ms.obj_array:
                gen_matrix_align_x(ms.obj_array, self.p)
                gen_matrix_align_y(ms.obj_array, self.p)

                # calculate matrix height
                ms.size.min_y = gen_bound(ms.parent_coll, 'y', 'min')
                ms.size.max_y = gen_bound(ms.parent_coll, 'y', 'max')
                bracket_type = matrix_brackets[ms.brackets]

                if not ms.brackets == 'matrix':
                    # generate left bracket of matrix
                    gen_text_object(self.p, self.d, bracket_type[0], 'math')
                    gen_brackets(self.d.context.active_object, self.p, ms.mx_coll, ms.size)

                    # calculate furthest x position
                    ms.size.max_x = gen_bound(ms.parent_coll, 'x', 'max') + ms.size.bracket_width / 2.0

                    # generate right bracket of matrix
                    gen_text_object(self.p, self.d, bracket_type[1], 'math')
                    gen_brackets(self.d.context.active_object, self.p, ms.mx_coll, ms.size)

                # center matrix into row
                gen_matrix_center(ms.mx_coll, ms.size, ms.init_params.height)

                # set new width and old height
                self.p.width = gen_bound(ms.mx_coll, 'x', 'max') + BASE_SPACE * self.d.text_scale
                self.p.height = ms.init_params.height

                # link objects to matrix collection
                for row in ms.obj_array:
                    for coll_name in row:
                        gen_join_collections(coll_name, ms.mx_coll)

            # join matrix collection into parent collection
            gen_join_collections(ms.mx_coll, ms.parent_coll)
            self.d.current_coll = ms.parent_coll  # set current collection
            return True

        else:
            print(f"Unknown action '{action}'")
            return False

    # main function for parsing process
    def parse(self):
        # parsing loop
        while self.stack:
            stack_top = self.stack[-1]
            token = self.lex.peek_token()

            if self.math_mode_end(stack_top, token):
                # recalculate position before changing modes
                gen_calculate(self.p, self.d.text_scale, self.levels)
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
                    print(f"Syntax error: Expected '{stack_top}' but got '{token.value}'")
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
                    print(f"Syntax error: No rule for ({stack_top}, {token.type}, {token.value})")
                    return False

        if self.stack:
            err = "Not all tokens have been read!"
            print("Syntax error:", err)
            return False
