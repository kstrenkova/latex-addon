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
# TODO research what the default value should be for \par and for itemize
# TODO inline mode and display mode differences
# TODO custom bullet points don't work for enumerate


class ItemizeState:
    def __init__(self, nest_lvl):
        self.bullet_number = 0
        self.bullet_type = '\u2022'
        self.nest_lvl = nest_lvl


class SyntaxAnalyser:
    def __init__(self, lex, context, custom_prop):
        self.stack = ['$', 'PROG']
        self.state_stack = []
        self.block = []

        self.lex = lex
        self.d = Defaults(context, custom_prop)
        self.p = Parameters(custom_prop.text_scale, 0.0, 0.0, 0.0)


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


    # TODO add mode differences
    # function calls the mathematical syntax analyser
    def enter_math_mode(self):
        # When we use blocks we don't want to consume token and when we use symbols we do
        # How to change this to a clear version is the TODO
        token = self.lex.peek_token()
        if token.value in ['$', '\(', '\[']:
            self.lex.get_token()

        latex_coll = self.d.base_coll
        self.d.current_coll = gen_new_collection("MathematicalEqCollection", self.d.base_coll)
        self.d.base_coll = self.d.current_coll

        # activate the collection for mathematical equations
        gen_set_active_collection(latex_coll, self.d.current_coll)

        # call math syntax analyser
        math_syntax = MathSyntaxAnalyser(self.lex, self.d, self.p)
        self.lex.mode = "math"

        print("Entering math mode!")

        if not math_syntax.parse():
            warn_msg = 'Mathematical equation was not fully generated.'
            print(warn_msg)
            return False

        self.lex.mode = "text"
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
            action = block_actions.get(self.block[-1])
            return self.execute_action(action)

        elif action == '#ACTION_BLOCK_VERIFY_BEGIN':
            token = self.lex.get_token()
            if block_actions.get(token.value) is not None:
                self.block.append(token.value)
                return True

            print("Block value", token.value, "is not correct or supported!")
            return False

        elif action == '#ACTION_BLOCK_VERIFY_END':
            token = self.lex.get_token()
            if token.value == self.block[-1]:
                self.block.pop()
                return True

            print("Block value in begin", self.block[-1], "doesn't match the value in end", token.value)
            return False

        # <CONST> actions
        elif action == '#ACTION_GENERATE_TEXT':
            token = self.lex.get_token()
            gen_text_object(self.p, self.d.current_coll, token.value, self.d.user_font)
            return True

        # new line (\\)
        elif action == '#ACTION_NEW_LINE':
            token = self.lex.peek_token()

            # consume token when enter is explicitely used
            if token.type == '_ENTER':
                self.lex.get_token()

            gen_adjust_new_line(self.p)
            return True

        # paragraph (\par)
        elif action == '#ACTION_PARAGRAPH':
            self.execute_action('#ACTION_NEW_LINE')
            self.p.width = PAR_SPACE
            return True

        # <ITEMIZE> actions
        elif action == '#ACTION_INIT_ITEM':
            # calculate the level of nesting
            nested_level = 1
            for state in self.state_stack:
                if isinstance(state, ItemizeState):
                    nested_level += 1

            # add a new itemize/enumerate block
            self.state_stack.append(ItemizeState(nested_level))
            return True

        elif action == '#ACTION_SAVE_ITEM':
            # overwrite default bullet point value
            token = self.lex.get_token()
            its = self.state_stack[-1]
            its.bullet_type = token.value
            return True

        elif action == '#ACTION_ADD_ITEM':
            # get bullet point value
            its = self.state_stack[-1]
            if self.block[-1] == 'itemize':
                item = its.bullet_type
            elif self.block[-1] == 'enumerate':
                its.bullet_number += 1
                item = str(its.bullet_number) + '.'

            # generate bullet point
            gen_text_object(self.p, self.d.current_coll, item, self.d.user_font)
            gen_bullet_point(self.p, its.nest_lvl)
            its.bullet_type = '\u2022'
            return True

        elif action == '#ACTION_END_ITEM':
            # set new line when main itemize/enumerate end
            its = self.state_stack[-1]
            if its.nest_lvl == 1:
                self.execute_action("#ACTION_NEW_LINE")
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

            gen_text_object(self.p, self.d.current_coll, content, 'verb')
            return True

        # MATH MODE
        elif action.startswith('#ACTION_MATH_MODE_'):
            self.d.math_mode = action.removeprefix('#ACTION_MATH_MODE_').lower()
            return self.enter_math_mode()

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

            # generate space and consume the whitespace token
            if token.type == "WHITESPACE":
                self.p.width += BASE_SPACE * self.p.scale
                self.lex.get_token()
                continue

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
