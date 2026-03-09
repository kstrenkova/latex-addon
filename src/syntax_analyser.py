# ---------------------------------------------------------------------------
# File name   : syntax_analyser.py
# Created By  : Katarina Strenkova
# ---------------------------------------------------------------------------

import bpy

from .generator import *
from .syntax_analyser_math import MathSyntaxAnalyser
from .syntax_utils import Defaults, Parameters, preload_fonts

from .data.ll_table import *
from .data.characters_db import *

# TODO [bug] Start creating objects on cursor point not at 0.0
# TODO [fix] Make multicolumn content move if it's aligned right and has multiple vlines at the end
# TODO [fix] Verb command should have spaces based on word spacing parameter
# TODO [feature] Add mathfonts not used only on upper letters
# TODO [feature] Add material to different mesh types
# TODO [feature] Make setting width work for tables
# TODO [feature] Add loadbar next to mouse when generating objects


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
        self.align = 'c'
        self.before = 0
        self.after = 0

    def reset_col_span(self):
        self.span = 1
        self.align = 'c'
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


# TODO set last_min_y properly
class TableCellConstraint:
    def __init__(self):
        self.max_width = None
        self.init_cell_x = -1
        self.init_row_y = -1
        self.last_min_y = 0.0
        self.cell_objects = []

    def set_init_pos(self, width, height):
        self.init_cell_x = width
        self.init_row_y = height
        self.last_min_y = 0.0

    def set_column_width(self, columns, col):
        if len(columns) <= col:
            return

        # save width constraint if it's positive
        p_width = columns[col].width
        if p_width > 0:
            self.max_width = self.init_cell_x + p_width

    def reset_cell_constraint(self):
        self.max_width = None
        self.init_cell_x = -1
        self.init_row_y = -1
        self.last_min_y = 0.0
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


class SyntaxAnalyser:
    def __init__(self, lex, context, custom_prop):
        self.stack = ['$$$', 'PROG']
        self.state_stack = []
        self.block = []

        self.lex = lex
        self.d = Defaults(context, custom_prop)
        self.p = Parameters(custom_prop.text_scale, 0.0, 0.0, 0.0)
        self.cell_con = TableCellConstraint()

    # function finds first state of specific type from top of stack
    def get_context_state(self, state_type):
      for state in reversed(self.state_stack):
          if isinstance(state, state_type):
              return state
      return None

    # function consumes redundant whitespaces from string
    def consume_whitespace(self):
        self.d.whitespace = False
        token = self.lex.peek_token(True)
        if token.type == 'WHITESPACE':
            token = self.lex.get_token(True)

    # function returns the next rule
    def choose_rule(self, stack_top, token):
        key = token.value if token.type == 'COMMAND' else token.type

        # special epsilon rules
        if stack_top in epsilon_rules and (token.type, token.value) not in epsilon_rules[stack_top]:
            key = 'epsilon'

        if stack_top == 'PROG':
            key = '_ANY'

        # special rule for item custom bullet point context
        its = self.get_context_state(ItemizeState)
        if token.value == ']' and its and its.custom_bullet:
            its.custom_bullet = False
            return ['epsilon']

        print("Stack top:", stack_top)
        print("KEY:", key)
        rule = ll_table.get((stack_top, key))
        return rule


    # function calls the mathematical syntax analyser
    def enter_math_mode(self):
        # change starting position for display mode
        if self.d.math_mode == 'display':
            self.execute_action('#ACTION_NEW_LINE')

        # save currently used collections
        text_current_coll = self.d.current_coll
        latex_base_coll = self.d.base_coll

        # generate collection for math mode
        self.d.current_coll = gen_new_collection("MathematicalEqCollection", latex_base_coll)
        self.d.base_coll = self.d.current_coll

        # activate the collection for mathematical equations
        gen_set_active_collection(latex_base_coll, self.d.current_coll)

        print("Entering math mode!")

        # call math syntax analyser
        math_syntax = MathSyntaxAnalyser(self.lex, self.d, self.p)
        if not math_syntax.parse():
            warn_msg = 'Mathematical equation was not fully generated.'
            print(warn_msg)
            return False

        self.d.base_coll = latex_base_coll
        print("Returned from math mode!")

        # consume redundant whitespace
        self.consume_whitespace()

        # change ending position for display mode
        if self.d.math_mode == 'display':
            self.execute_action('#ACTION_NEW_LINE')

        # join collection into parent collection
        gen_join_collections(self.d.current_coll, text_current_coll)
        gen_activate_collection(self.d.base_coll)
        self.d.current_coll = text_current_coll
        return True


    # function executes given action
    def execute_action(self, action):
        # ignore whitespaces
        if action not in whitespace_add_actions:
            self.consume_whitespace()

        # <BLOCK> actions
        if action == '#ACTION_BLOCK_ENTER':
            action = block_actions.get(self.block[-1])

            # define starting rule for the environment
            if self.block[-1] in ['itemize', 'enumerate']:
                rule = ['ITEMIZE']
            elif self.block[-1] == 'tabular':
                rule = ['{', 'ALIGN', '}', 'TABLE']
            else:
                rule = ['MORE_TERM']

            # add starting rule to the stack
            for symbol in reversed(rule):
                self.stack.append(symbol)

            return self.execute_action(action)

        elif action == '#ACTION_BLOCK_VERIFY_BEGIN':
            token = self.lex.get_token()
            if block_actions.get(token.value) is not None:
                self.block.append(token.value)
                return True

            err = f"Block value '{token.value}' is not correct or supported!"
            print("Syntax error:", err)
            return False

        elif action == '#ACTION_BLOCK_VERIFY_END':
            token = self.lex.get_token()
            if token.value == self.block[-1]:
                self.block.pop()
                return True

            err = f"Block value in begin '{self.block[-1]}' doesn't match the value in end '{token.value}!'"
            print("Syntax error:", err)
            return False

        # <CONST> actions
        elif action == '#ACTION_GENERATE_TEXT':
            token = self.lex.get_token()
            gen_text_object(self.p, self.d, token.value, self.d.user_font)

            # warp objects in cell that has width constraint
            if gen_wrap_obj_in_cell(self.p, self.d, self.cell_con):
                self.consume_whitespace()
            return True

        # new line (\\)
        elif action == '#ACTION_NEW_LINE':
            gen_adjust_new_line(self.p, self.d.base_coll, self.d.line_height)
            return True

        # paragraph (\par)
        elif action == '#ACTION_PARAGRAPH':
            self.execute_action('#ACTION_NEW_LINE')
            self.p.width = self.d.block_space
            return True

        # <ITEMIZE> actions
        elif action == '#ACTION_ITEM_INIT':
            # get all previous itemize/enumerate environments
            nest_array = []
            its = self.get_context_state(ItemizeState)
            if its:
                nest_array = its.nest_array.copy()

            # save current environment
            nest_array.append(self.block[-1])

            # add a new itemize/enumerate block
            self.state_stack.append(ItemizeState(self.d.current_coll, nest_array))
            return True

        elif action == '#ACTION_ITEM_SAVE_INIT':
            its = self.state_stack[-1]
            its.custom_bullet = True

            # create new collection for bullet point
            bpcoll = gen_new_collection("BulletPointCollection", self.d.current_coll)
            self.d.current_coll = bpcoll
            return True

        elif action == '#ACTION_ITEM_SAVE_ADD':
            its = self.state_stack[-1]
            nest_lvl = get_nest_level(its.nest_array, self.block[-1])

            # get objects from bullet point collection
            bpcoll = bpy.data.collections.get(self.d.current_coll)
            gen_bullet_point(list(bpcoll.objects), self.p, self.d, len(its.nest_array))

            # join bullet point collection into parent collection
            gen_join_collections(self.d.current_coll, its.parent_coll)
            self.d.current_coll = its.parent_coll
            return True

        elif action == '#ACTION_ITEM_ADD':
            its = self.state_stack[-1]
            nest_lvl = get_nest_level(its.nest_array, self.block[-1])

            # use default bullet point
            if self.block[-1] == 'itemize':
                item = get_bullet_default(nest_lvl)
            elif self.block[-1] == 'enumerate':
                its.bullet_number += 1
                item = get_numbering_default(nest_lvl, its.bullet_number)

            # generate bullet point
            gen_text_object(self.p, self.d, item, self.d.user_font)
            gen_bullet_point([bpy.context.active_object], self.p, self.d, len(its.nest_array))
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
        elif action == '#ACTION_VERB_GENERATE':
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
            content, err = self.lex.get_token_until(['_TEXT'], '}')
            if len(err) > 0:
                print("Syntax error:", err)
                return False

            # get alignment width for the current column
            align = ts.align.columns[-1]
            err = parse_table_width(align, content, 'column')
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
            self.execute_action('#ACTION_TABLE_NEW_CELL')
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

            # move only for the first cline in one row
            if ts.hline.cline_new:
                self.p.line.height -= SMALL_SPACE * self.p.scale
                self.p.line.min_y -= SMALL_SPACE * self.p.scale
                ts.hline.cline_new = False

            # save position of the horizontal line
            ts.hline.cline_pos.append(self.p.line.min_y)

            # get cline range string
            content, err = self.lex.get_token_until(['_TEXT'], '}')
            if len(err) > 0:
                print("Syntax error:", err)
                return False

            # parse cline range string
            cline_range, err = parse_cline_range(content)
            if len(err) > 0:
                print("Syntax error:", err)
                return False

            ts.hline.cline_range.append(cline_range)
            return True

        elif action in ('#ACTION_TABLE_MULTICOL_NUMBER', '#ACTION_TABLE_MULTIROW_NUMBER'):
            ts = self.state_stack[-1]
            content, err = self.lex.get_token_until(['_TEXT'], '}')
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
            content, err = self.lex.get_token_until(['_TEXT', '_PIPE'], '}')
            if len(err) > 0:
                print("Syntax error:", err)
                return False

            # save alignment and overwrite vertical lines
            err = parse_multicol_alignment(ts.multi, content)
            if len(err) > 0:
                print("Syntax error:", err)
                return False

            return True

        elif action == '#ACTION_TABLE_MULTIROW_WIDTH':
            ts = self.state_stack[-1]
            content, err = self.lex.get_token_until(['_TEXT'], '}')
            if len(err) > 0:
                print("Syntax error:", err)
                return False

            err = parse_table_width(ts.multi.row, content, '\\multirow', True)
            if len(err) > 0:
                print("Syntax error:", err)
                return False

            return True

        elif action == '#ACTION_TABLE_NEW_ROW':
            ts = self.state_stack[-1]

            # special info saving for multicolumn
            save_multicol_info(ts)

            # add new array that represents row
            ts.obj_array.append([])
            self.execute_action('#ACTION_TABLE_NEW_CELL')  # initial cell

            # set width to start
            self.p.width = ts.init_params.width

            # set height lower and record the y positions
            start_y = self.p.line.min_y
            gen_adjust_new_line(self.p, self.d.base_coll, self.d.line_height, ts.init_params.width)
            end_y = self.p.line.min_y - (SMALL_SPACE * self.p.scale)

            # save row y positions
            ts.align.row_y.append((start_y, end_y))
            return True

        elif action == '#ACTION_TABLE_NEW_CELL':
            # reset cell constraint and initial height
            if self.cell_con.max_width is not None:
                self.p.line.height = self.cell_con.init_row_y
            self.cell_con.reset_cell_constraint()

            ts = self.state_stack[-1]
            ts.hline.reset_cline()  # mark end of consequent cline commands

            # special info saving for multicolumn
            save_multicol_info(ts)

            # add table cell collection to row
            self.d.current_coll = gen_new_collection("TableCellCollection", ts.table_coll)
            row = ts.obj_array[ts.get_row_num()]
            row.append(self.d.current_coll)

            if len(row) > len(ts.align.columns):
                err = f"Table has more columns than defined in column specification!"
                print("Syntax error:", err)
                return False

            # save cell constraint
            if ts.multi.col.span == 1 and ts.multi.row.span == 1:
                self.cell_con.set_init_pos(self.p.width, self.p.line.height)
                self.cell_con.set_column_width(ts.align.columns, len(row) - 1)

            return True

        elif action == '#ACTION_TABLE_CREATE':
            ts = self.state_stack.pop()
            gen_cleanup_last_row(ts.obj_array)

            # position table if not empty
            if len(ts.obj_array):
                gen_table_align_x(ts.obj_array, self.p, ts.align, ts.multi)
                gen_table_align_y(ts.obj_array, ts.align, ts.multi)

            # link objects to table collection
            for row in ts.obj_array:
                for coll_name in row:
                    gen_join_collections(coll_name, ts.table_coll)

            # generate all table lines
            gen_table_lines(self.d.context, ts)

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
        collection = bpy.data.collections.new("LaTeXCollection")
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
                self.lex.get_token(True)
                self.d.whitespace = True
                continue

            # successful parsing
            if stack_top == '$$$' and token.type == 'END':
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

            # add whitespace if one is pending
            if self.d.whitespace:
                self.p.width += self.d.word_space * self.p.scale
                self.d.whitespace = False

        # put a new line at the end of the document
        self.execute_action("#ACTION_NEW_LINE")

        # verify that all tokens have been read
        if self.stack:
            print("Error, not all tokens have been read!")
            return False

        # select all objects in base collection
        for obj in bpy.data.collections[collection.name].all_objects:
            obj.select_set(True)

        return True
