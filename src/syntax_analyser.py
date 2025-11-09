# ---------------------------------------------------------------------------
# File name   : syntax_analyser.py
# Created By  : Katarina Strenkova
# ---------------------------------------------------------------------------

import bpy

from .generator import *
from .syntax_analyser_math import MathSyntaxAnalyser
from .syntax_utils import Defaults, Parameters, preload_fonts, change_font

# TODO get rid of ..data
from ..data.ll_table import *
from ..data.characters_db import *

# TODO checkout mathfonts not used only on upper letters
# TODO new line should take the height of the object into account
# TODO extra space after symbols like (, ) that are not _TEXT


class ItemizeState:
    def __init__(self):
        self.bullet_number = 0
        self.bullet_type = '\u2022'


class SyntaxAnalyser:
    def __init__(self, lex, context, custom_prop):
        self.stack = ['$', 'PROG']
        self.state_stack = []

        self.lex = lex
        self.d = Defaults(context, custom_prop)
        self.p = Parameters(custom_prop.text_scale, 0.0, 0.0, 0.0)
        self.block = ''


    # function returns the next rule
    def choose_rule(self, stack_top, token):
        # TODO clean lookup
        key = token.value if (token.type in special_token_type) else token.type

        if stack_top in epsilon_rules and epsilon_rules[stack_top] != (token.type, token.value):
            key = 'epsilon'

        if stack_top == 'PROG':
            key = '_ANY'

        print("KEY:", key)
        rule = ll_table.get((stack_top, key))
        return rule


    # function creates a new text object with given value and font,
    # then moves it according to context
    def create_text_object(self, value, font_type):
        gen_text(value, change_font(font_type), self.d.current_coll, self.p.line)

        self.p.height = self.p.line.height
        gen_move_position(self.p)
        self.p.width += BASE_SPACE * self.p.scale  # space between text
        return True


    # function sets the active collection
    def set_active_collection(self, base_coll, current_coll):
        view_layer = bpy.context.view_layer
        collection = view_layer.layer_collection.children[base_coll].children[current_coll]
        view_layer.active_layer_collection = collection


    # TODO add mode differences
    # function calls the mathematical syntax analyser
    def enter_math_mode(self, mode):
        # When we use blocks we don't want to consume token and when we use symbols we do
        # How to change this to a clear version is the TODO
        token = self.lex.peek_token()
        if token.value in ['$', '\(', '\[']:
            self.lex.get_token()

        latex_coll = self.d.base_coll
        self.d.current_coll = gen_new_collection("MathematicalEqCollection", self.d.base_coll)
        self.d.base_coll = self.d.current_coll

        # activate the collection for mathematical equations
        self.set_active_collection(latex_coll, self.d.current_coll)

        # call math syntax analyser
        math_syntax = MathSyntaxAnalyser(self.lex, self.d, self.p)

        print("Entering math mode!")

        if not math_syntax.parse():
            warn_msg = 'Mathematical equation was not fully generated.'
            print(warn_msg)
            return False

        self.d.base_coll = latex_coll
        print("Returned from math mode!")

        # join collection into parent collection
        gen_join_collections(self.d.current_coll, self.d.base_coll)
        gen_activate_collection(self.d.base_coll)
        self.d.current_coll = latex_coll
        return True


    # function executes given action
    def execute_action(self, action):
        # <BLOCK> actions
        if action == '#ACTION_BLOCK_ENTER':
            action = block_actions.get(self.block)
            return self.execute_action(action)

        elif action == '#ACTION_BLOCK_VERIFY_BEGIN':
            token = self.lex.get_token()
            if block_actions.get(token.value) is not None:
                self.block = token.value
                return True

            print("Block value", token.value, "is not correct or supported!")
            return False

        elif action == '#ACTION_BLOCK_VERIFY_END':
            token = self.lex.get_token()
            if token.value == self.block:
                self.block = ''
                return True

            print("Block value in begin", self.block, "doesn't match the value in end", token.value)
            return False

        # <CONST> actions
        elif action == '#ACTION_GENERATE_TEXT':
            token = self.lex.get_token()
            return self.create_text_object(token.value, self.d.user_font)

        # TODO new line based on line height
        elif action == '#ACTION_NEW_LINE':
            token = self.lex.peek_token()

            if token.type == '_ENTER':
                self.lex.get_token()

            # current lowest and highest point
            min_y = gen_bound_for_array(self.p.line.line_objs, 'y', 'min')
            max_y = gen_bound_for_array(self.p.line.line_objs, 'y', 'max')

            lmin_y = self.p.line.min_y  # lowest point of last row
            overflow = max_y - lmin_y if (max_y > lmin_y) else 0

            # move objects down
            for obj in self.p.line.line_objs:
                obj.location.y -= overflow

            self.p.line.min_y = min_y

            # reset line objects
            self.p.line.line_objs.clear()

            self.p.line.height = self.p.line.min_y - LINE_SPACE
            self.p.width = 0.0
            return True

        elif action == '#ACTION_PARAGRAPH':
            # TODO
            tmp = self.execute_action('#ACTION_NEW_LINE')
            self.p.width = 1.0  # TODO research what the default value should be (for itemize as well)
            return True

        # <ITEMIZE> actions
        elif action == '#ACTION_INIT_ITEM':
            its = ItemizeState()
            self.state_stack.append(its)
            return True

        elif action == '#ACTION_SAVE_ITEM':
            token = self.lex.get_token()
            its = self.state_stack[-1]
            its.bullet_type = token.value
            return True

        elif action == '#ACTION_ADD_ITEM':
            its = self.state_stack[-1]
            if self.block == 'itemize':
                item = its.bullet_type
            elif self.block == 'enumerate':
                its.bullet_number += 1
                item = str(its.bullet_number) + '.'

            gen_bullet_point(self.p, self.d, item)
            its.bullet_type = '\u2022'
            return True

        elif action == '#ACTION_END_ITEM':
            self.state_stack.pop()
            return True

        # <FONT CHANGE> actions
        elif action.startswith('#ACTION_FONT_'):
            self.d.user_font = action.removeprefix('#ACTION_FONT_').lower()
            return True

        # verb command
        elif action == '#ACTION_GENERATE_VERB':
            content, err = self.lex.get_verb_content()
            if len(err) > 0:
                print("Error:", err)
                return False

            return self.create_text_object(content, 'verb')

        # MATH MODE
        elif action.startswith('#ACTION_MATH_MODE_'):
            mode = action.removeprefix('#ACTION_MATH_MODE_').lower()
            return self.enter_math_mode(mode)

        else:
            print(f"Unknown action: '{action}'")
            return False


    # main function for parsing process
    def parse(self):
        # creating base collection
        collection = bpy.data.collections.new("LatexCollection")
        bpy.context.scene.collection.children.link(collection)
        gen_activate_collection(collection.name)

        self.d.base_coll = collection.name
        self.d.current_coll = collection.name

        preload_fonts(self.d.fonts)

        # parsing loop
        while self.stack:
            stack_top = self.stack[-1]
            token = self.lex.peek_token()
            print(f"STACK: {self.stack}")
            print(f"Token type: '{token.type}'")
            print(f"Token value: '{token.value}'")

            # successful parsing
            if stack_top == '$' and token.type == 'END':
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
                #TODO cleanup
                terminal = token.value if token.type != 'dollar' else token.type

                if stack_top == terminal:
                    self.stack.pop()
                    self.lex.get_token()
                else:
                    print(f"Syntax Error: Expected '{stack_top}' but got '{terminal}'")
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

        # select all objects in base collection
        for obj in bpy.data.collections[collection.name].all_objects:
            obj.select_set(True)

        return True
