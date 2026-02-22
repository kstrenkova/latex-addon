# ---------------------------------------------------------------------------
# File name   : syntax_analyser.py
# Created By  : Katarina Strenkova
# ---------------------------------------------------------------------------

import bpy

from .generator import *
from .syntax_analyser_math import MathSyntaxAnalyser
from .syntax_utils import Defaults, Parameters, preload_fonts

# TODO get rid of ..data
from ..data.ll_table import *
from ..data.characters_db import *

# TODO checkout mathfonts not used only on upper letters
# TODO research what the default value should be for \par and for itemize
# TODO [feature] add \newline
# TODO [bug] Whitespaces are making mess in the first cell of table


class ItemizeState:
    def __init__(self, nest_array):
        self.bullet_number = 0
        self.custom_bullet = ''
        self.nest_array = nest_array


# single column alignment
class ColumnAlignment:
    def __init__(self, type):
        self.type = type
        self.width = -1
        self.unit = ''


# whole table alignment
class TableAlignment:
    def __init__(self):
        self.columns = []
        self.vline = []
        self.vline_pos = []
        self.column_width = []


class TableHorizontalLines:
    def __init__(self):
        self.hline_pos = []
        self.cline_pos = []
        self.cline_range = []

    def save_cline_range(self, start, end):
        self.cline_range.append((start, end))


class TableMultiCell:
    def __init__(self):
        self.col_span = 1
        self.row_span = 1
        self.col_align = 'c'
        self.row_width = -1
        self.cell_span = {}

    def reset_col_span(self):
        self.col_span = 1
        self.col_align = 'c'

    def reset_row_span(self):
        self.row_span = 1
        self.row_width = -1


class TableState:
    def __init__(self, parent_coll, init_params):
        self.parent_coll = parent_coll
        self.init_params = init_params
        self.table_coll = ''
        self.obj_array = [[]]
        self.row_num = 0
        self.align = TableAlignment()
        self.hline = TableHorizontalLines()
        self.multi = TableMultiCell()


class SyntaxAnalyser:
    def __init__(self, lex, context, custom_prop):
        self.stack = ['$$$', 'PROG']
        self.state_stack = []
        self.block = []

        self.lex = lex
        self.d = Defaults(context, custom_prop)
        self.p = Parameters(custom_prop.text_scale, 0.0, 0.0, 0.0)


    # function returns the next rule
    def choose_rule(self, stack_top, token):
        key = token.value if token.type == 'COMMAND' else token.type

        if stack_top in epsilon_rules and (token.type, token.value) not in epsilon_rules[stack_top]:
            key = 'epsilon'

        if stack_top == 'PROG':
            key = '_ANY'

        print("KEY:", key)
        rule = ll_table.get((stack_top, key))
        return rule


    # function calls the mathematical syntax analyser
    def enter_math_mode(self):
        token = self.lex.peek_token()

        # change starting position for display mode
        if self.d.math_mode == 'display':
            self.execute_action('#ACTION_NEW_LINE')

        latex_coll = self.d.base_coll
        self.d.current_coll = gen_new_collection("MathematicalEqCollection", self.d.base_coll)
        self.d.base_coll = self.d.current_coll

        # activate the collection for mathematical equations
        gen_set_active_collection(latex_coll, self.d.current_coll)

        # call math syntax analyser
        math_syntax = MathSyntaxAnalyser(self.lex, self.d, self.p)

        print("Entering math mode!")

        if not math_syntax.parse():
            warn_msg = 'Mathematical equation was not fully generated.'
            print(warn_msg)
            return False

        self.d.base_coll = latex_coll
        print("Returned from math mode!")

        # consume redundant whitespace
        token = self.lex.peek_token()
        if token.type == 'WHITESPACE':
            self.lex.get_token()

        # change ending position for display mode
        if self.d.math_mode == 'display':
            self.execute_action('#ACTION_NEW_LINE')

        # join collection into parent collection
        gen_join_collections(self.d.current_coll, self.d.base_coll)
        gen_activate_collection(self.d.base_coll)
        self.d.current_coll = latex_coll
        return True


    # function executes given action
    def execute_action(self, action):
        # <BLOCK> actions
        if action == '#ACTION_BLOCK_ENTER':
            action = block_actions.get(self.block[-1])
            return self.execute_action(action)

        elif action == '#ACTION_BLOCK_VERIFY_BEGIN':
            token = self.lex.get_token()
            if block_actions.get(token.value) is not None:
                self.block.append(token.value)
                return True

            print("Block value '{token.value}' is not correct or supported!")
            return False

        elif action == '#ACTION_BLOCK_VERIFY_END':
            token = self.lex.get_token()
            if token.value == self.block[-1]:
                self.block.pop()
                return True

            print("Block value in begin '{self.block[-1]}' doesn't match the value in end '{token.value}!'")
            return False

        # <CONST> actions
        elif action == '#ACTION_GENERATE_TEXT':
            token = self.lex.get_token()
            gen_text_object(self.p, self.d, token.value, self.d.user_font)
            return True

        # new line (\\)
        elif action == '#ACTION_NEW_LINE':
            gen_adjust_new_line(self.p, self.d.base_coll, LINE_SPACE)
            return True

        # paragraph (\par)
        elif action == '#ACTION_PARAGRAPH':
            self.execute_action('#ACTION_NEW_LINE')
            self.p.width = PAR_SPACE
            return True

        # <ITEMIZE> actions
        elif action == '#ACTION_ITEM_INIT':
            # save current environment
            nest_array = []
            for state in reversed(self.state_stack):
                if isinstance(state, ItemizeState):
                    nest_array = state.nest_array.copy()
                    break

            nest_array.append(self.block[-1])

            # add a new itemize/enumerate block
            self.state_stack.append(ItemizeState(nest_array))
            return True

        elif action == '#ACTION_ITEM_SAVE':
            # overwrite default bullet point value
            # TODO save all items, even commands
            token = self.lex.get_token()
            its = self.state_stack[-1]
            its.custom_bullet = token.value
            return True

        elif action == '#ACTION_ITEM_ADD':
            its = self.state_stack[-1]
            nest_lvl = get_nest_level(its.nest_array, self.block[-1])

            if len(its.custom_bullet) != 0:
                # use custom bullet point
                item = its.custom_bullet
                its.custom_bullet = ''
            else:
                # use default bullet point
                if self.block[-1] == 'itemize':
                    item = get_bullet_default(nest_lvl)
                elif self.block[-1] == 'enumerate':
                    its.bullet_number += 1
                    item = get_numbering_default(nest_lvl, its.bullet_number)

            # generate bullet point
            gen_text_object(self.p, self.d, item, self.d.user_font)
            gen_bullet_point(self.p, len(its.nest_array))
            return True

        elif action == '#ACTION_ITEM_END':
            its = self.state_stack.pop()

            # set new line when main itemize/enumerate end
            if len(its.nest_array) == 1:
                self.execute_action("#ACTION_NEW_LINE")
            return True

        # <FONT CHANGE> actions
        elif action.startswith('#ACTION_FONT_'):
            self.d.user_font = action.removeprefix('#ACTION_FONT_').lower()
            return True

        # verb command
        elif action == '#ACTION_GENERATE_VERB':
            content, err = self.lex.get_verb_content()
            if len(err) > 0:
                print("Syntax error:", err)
                return False

            gen_text_object(self.p, self.d, content, 'verb')
            return True

        # MATH MODE
        elif action.startswith('#ACTION_MATH_MODE_'):
            self.d.math_mode = action.removeprefix('#ACTION_MATH_MODE_').lower()
            return self.enter_math_mode()

        # <TABLE> actions
        elif action == '#ACTION_ALIGN_SAVE':
            token = self.lex.get_token()
            ts = self.state_stack[-1]

            # save individual letters as column alignment
            for c in token.value:
                ts.align.columns.append(ColumnAlignment(c))
                if c not in table_alignments:
                    err = f"Tabular alignment '{align.type}' is not correct or supported!"
                    print("Syntax error:", err)
                    return False

            return True

        elif action == '#ACTION_ALIGN_LINE':
            ts = self.state_stack[-1]

            # add vertical line before the current column
            column = len(ts.align.columns)

            if len(ts.align.vline) <= column:
                # add zeros to match the number of the current column
                zero_num = (column + 1) - len(ts.align.vline)
                ts.align.vline.extend([0] * zero_num)

            ts.align.vline[column] += 1
            return True

        elif action == '#ACTION_COL_WIDTH':
            ts = self.state_stack[-1]
            content, err = self.lex.get_token_until('_TEXT', '}')
            if len(err) > 0:
                print("Syntax error:", err)
                return False

            # get alignment width for the current column
            align = ts.align.columns[-1]
            err = get_alignment_width(align, content)
            if len(err) > 0:
                print("Syntax error:", err)
                return False

            return True

        elif action == '#ACTION_TABLE_INIT':
            ts = TableState(self.d.current_coll, self.p.create_copy())
            self.state_stack.append(ts)

            # table body collection
            ts.table_coll = gen_new_collection("TableBodyCollection", ts.parent_coll)

            # first table cell collection
            self.d.current_coll = gen_new_collection("TableCellCollection", ts.table_coll)
            ts.obj_array[ts.row_num].append(self.d.current_coll)
            return True

        elif action == '#ACTION_TABLE_HLINE':
            ts = self.state_stack[-1]
            self.p.line.height -= SMALL_SPACE * self.p.scale
            self.p.line.min_y -= SMALL_SPACE * self.p.scale

            # save position of the horizontal line
            ts.hline.hline_pos.append(self.p.line.min_y)
            return True

        elif action == '#ACTION_TABLE_CLINE':
            ts = self.state_stack[-1]
            self.p.line.height -= SMALL_SPACE * self.p.scale
            self.p.line.min_y -= SMALL_SPACE * self.p.scale

            # save position of the horizontal line
            ts.hline.cline_pos.append(self.p.line.min_y)

            # get cline range string
            content, err = self.lex.get_token_until('_TEXT', '}')
            if len(err) > 0:
                print("Syntax error:", err)
                return False

            range, err = parse_cline_range(content)
            if len(err) > 0:
                print("Syntax error:", err)
                return False

            start, end = range
            ts.hline.save_cline_range(start, end)
            return True

        elif action in ('#ACTION_TABLE_MULTICOL_NUMBER', '#ACTION_TABLE_MULTIROW_NUMBER'):
            ts = self.state_stack[-1]
            content, err = self.lex.get_token_until('_TEXT', '}')
            if len(err) > 0:
                print("Syntax error:", err)
                return False

            err = get_multi_span_number(ts.multi, action, content)
            if len(err) > 0:
                print("Syntax error:", err)
                return False

            return True

        elif action == '#ACTION_TABLE_MULTICOL_ALIGN':
            ts = self.state_stack[-1]
            content, err = self.lex.get_token_until('_TEXT', '}')
            if len(err) > 0:
                print("Syntax error:", err)
                return False

            # TODO get alignment (only 1 + optional vertical lines)
            return True

        elif action == '#ACTION_TABLE_MULTIROW_WIDTH':
            ts = self.state_stack[-1]
            content, err = self.lex.get_token_until('_TEXT', '}')
            if len(err) > 0:
                print("Syntax error:", err)
                return False

            # TODO get width
            return True

        elif action == '#ACTION_TABLE_NEW_ROW':
            ts = self.state_stack[-1]

            # table cell collection
            self.d.current_coll = gen_new_collection("TableCellCollection", ts.table_coll)

            # add new array that represents row
            ts.obj_array.append([])
            ts.row_num += 1
            ts.obj_array[ts.row_num].append(self.d.current_coll)

            # set width to start and height lower
            self.p.width = ts.init_params.width
            gen_adjust_new_line(self.p, self.d.base_coll, LINE_SPACE, self.p.width)
            # TODO check out why it works with self.d.base_coll
            return True

        elif action == '#ACTION_TABLE_NEW_CELL':
            ts = self.state_stack[-1]

            # table cell collection
            self.d.current_coll = gen_new_collection("TableCellCollection", ts.table_coll)

            # add collection to row
            ts.obj_array[ts.row_num].append(self.d.current_coll)
            return True

        elif action == '#ACTION_TABLE_CREATE':
            ts = self.state_stack.pop()

            # position table
            gen_box_position_center(ts.obj_array, self.p, ts.align)

            # link objects to table collection
            for row in ts.obj_array:
                for coll_name in row:
                    gen_join_collections(coll_name, ts.table_coll)

            # gets the furthest x position
            body_coll = bpy.data.collections.get(ts.table_coll)
            if len(body_coll.all_objects):
                # TODO cleanup, make a function
                # TODO small overflow on vertical lines length
                y_pos = gen_bound(body_coll.name, 'y', 'max') + BASE_SPACE * self.p.scale
                line_length_y = gen_bound(body_coll.name, 'y', 'min') - y_pos - SMALL_SPACE * self.p.scale

                # generate all vertical lines
                for x_pos in ts.align.vline_pos:
                    gen_line_object(self.d.context, ts.init_params, ts.table_coll, x_pos, y_pos, line_length_y, 'y')

                line_length_x = gen_bound(body_coll.name, 'x', 'max') - ts.init_params.width

                # generate all horizontal lines (hline)
                for y_pos in ts.hline.hline_pos:
                    gen_line_object(self.d.context, ts.init_params, ts.table_coll, ts.init_params.width, y_pos, line_length_x)

                # generate all partial horizontal lines (cline)
                for y_pos, (start, end) in zip(ts.hline.cline_pos, ts.hline.cline_range):
                    # clamp start and end to number of columns
                    start = min(start, len(ts.align.column_width) - 1)
                    end = min(end, len(ts.align.column_width) - 1)

                    x_pos = ts.align.column_width[start - 1]
                    line_length_x = ts.align.column_width[end] - x_pos
                    gen_line_object(self.d.context, ts.init_params, ts.table_coll, x_pos, y_pos, line_length_x)

            # join table collection into parent collection
            gen_join_collections(ts.table_coll, ts.parent_coll)
            self.d.current_coll = ts.parent_coll  # set current collection
            return True

        else:
            print(f"Unknown action: '{action}'")
            return False


    # main function for parsing process
    def parse(self):
        # creating base collection
        collection = bpy.data.collections.new("LatexCollection")
        self.d.context.scene.collection.children.link(collection)
        gen_activate_collection(collection.name)

        self.d.base_coll = collection.name
        self.d.current_coll = collection.name

        preload_fonts(self.d.context, self.d.fonts)

        # parsing loop
        while self.stack:
            stack_top = self.stack[-1]
            token = self.lex.peek_token(True)  # also return whitespaces
            print(f"STACK: {self.stack}")
            print(f"Token type: '{token.type}'")
            print(f"Token value: '{token.value}'")

            # generate space and consume the whitespace token
            if token.type == "WHITESPACE":
                self.p.width += BASE_SPACE * self.p.scale
                self.lex.get_token(True)
                continue

            # successful parsing
            if stack_top == '$$$' and token.type == 'END':
                print("Success!")
                self.stack.pop()
                break

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

        # put a new line at the end of the document
        _ = self.execute_action("#ACTION_NEW_LINE")

        # verify that all tokens have been read
        if self.stack:
            print("Error, not all tokens have been read!")
            return False

        # select all objects in base collection
        for obj in bpy.data.collections[collection.name].all_objects:
            obj.select_set(True)

        return True
