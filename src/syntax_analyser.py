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

# TODO decide if bold and italic will be font change or object warp
# TODO decide which mathfont to implement
# TODO next fun thing -> itemize, enumerate


class ItemizeState:
    def __init__(self):
        self.bullet_type = '\u2022'
        self.bullet_number = 1


class SyntaxAnalyser:
    def __init__(self, lex, context, custom_prop):
        self.stack = ['$', 'PROG']
        self.state_stack = []

        self.lex = lex
        self.d = Defaults(context, custom_prop)
        self.parameters = Parameters(custom_prop.text_scale, 0.0, 0.0, 0.0)
        self.block_type = ''

    def choose_rule(self, stack_top, token):
        # TODO clean lookup
        if token.type in special_token_type:
            key = token.value
        else:
            key = token.type

        if (token.type, token.value) != ('COMMAND', 'item') and stack_top in ['ITEMIZE', 'ENUM']:
            key = "epsilon"

        if stack_top == "PROG":
            key = "_ANY"

        print("KEY:", key)
        rule = ll_table.get((stack_top, key))
        return rule

    def set_active_collection(self, base_coll, current_coll):
        view_layer = bpy.context.view_layer
        collection = view_layer.layer_collection.children[base_coll].children[current_coll]
        view_layer.active_layer_collection = collection

    def enter_block(self):
        # MATH INLINE MODE
        if self.block_type == 'math':
            return self.execute_action('#ACTION_MATH_INLINE_MODE')
        # MATH DISPLAY MODE
        elif self.block_type == 'equation':
            return self.execute_action('#ACTION_MATH_INLINE_MODE') # TODO
        elif self.block_type == 'displaymath':
            return self.execute_action('#ACTION_MATH_INLINE_MODE') # TODO

    def execute_action(self, action):
        # <CONST> actions
        if action == '#ACTION_GENERATE_TEXT':
            token = self.lex.get_token()
            gen_text(token.value, self.d.base_font, self.d.current_coll)
            self.parameters.height = self.parameters.line
            gen_move_position(self.parameters)
            return True

        if action == '#ACTION_NEW_LINE':
            token = self.lex.peek_token()
            if token.type == '_ENTER':
                self.lex.get_token()
            self.parameters.line -= 1.0
            self.parameters.width = 0.0
            return True

        # <BLOCK> actions
        elif action == '#ACTION_BLOCK_BEGIN':
            token = self.lex.get_token()

            if token.type == '_TEXT' and token.value in block_type:
                self.block_type = token.value
                return True

            print("This block value is not correct or supported!")
            return False

        elif action == '#ACTION_BLOCK_INIT':
            return self.enter_block()

        elif action == '#ACTION_BLOCK_END':
            token = self.lex.get_token()

            if token.type == '_TEXT' and token.value == self.block_type:
                self.block_type = ''
                return True

            print("The end block value doesn't match the begin block value.")
            return False

        elif action == '#ACTION_SAVE_ITEM':
            its = ItemizeState()
            token = self.lex.get_token()
            its.bullet_type = token.value
            self.state_stack.append(its)
            return True

        elif action == '#ACTION_ADD_ITEM':
            if self.state_stack and isinstance(self.state_stack[-1], ItemizeState):
                its = self.state_stack.pop()
                item = its.bullet_type
            else:
                item = '\u2022'
            gen_bullet_point(self.parameters, self.d, item)
            return True

        elif action == '#ACTION_ADD_ENUM':
            if self.state_stack and isinstance(self.state_stack[-1], ItemizeState):
                its = self.state_stack[-1]
                its.bullet_number += 1
            else:
                its = ItemizeState()
                self.state_stack.append(its)

            item = str(its.bullet_number) + '.'
            gen_bullet_point(self.parameters, self.d, item)
            return True

        elif action == '#ACTION_END_ENUM':
            self.state_stack.pop()
            return True

        # MATH INLINE MODE
        elif action == '#ACTION_MATH_INLINE_MODE':
            # When we use blocks we don't want to consume token and when we use symbols we do
            # How to change this to a clear version is the TODO
            token = self.lex.peek_token()
            if token.value in ['$', '\(', '\[']:
                self.lex.get_token()

            latex_coll = self.d.base_coll
            self.d.current_coll = gen_new_collection("MathematicalEqCollection", self.d.base_coll)

            # activate the collection for mathematical equations
            self.set_active_collection(latex_coll, self.d.current_coll)

            # call math syntax analyser
            math_syntax = MathSyntaxAnalyser(self.lex, self.d, self.parameters)

            print("Entering math mode!")

            if not math_syntax.parse():
                warn_msg = 'Mathematical equation was not fully generated. Check system console for more info on this matter.'
                # TODO self.report({'WARNING'}, warn_msg)
                return False

            self.d.base_coll = latex_coll
            print("Returned from math mode!")

            # join collection into parent collection
            gen_join_collections(self.d.current_coll, self.d.base_coll)
            gen_activate_collection(self.d.base_coll)
            self.d.current_coll = latex_coll
            return True

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

        # preload fonts
        preload_fonts()
        if self.d.base_font != "":
            self.d.base_font = bpy.data.fonts.load(self.d.base_font)

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
                print(f"Before action CT {token.value}")
                if not self.execute_action(action):
                    print(f"Action error: {action}")
                    return False

            # terminal
            elif not (stack_top.isupper() and stack_top != '$'):
                #TODO cleanup
                terminal = token.value if token.type in special_token_type else token.type

                if stack_top == terminal:
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

        # select all objects in base collection
        for obj in bpy.data.collections[collection.name].all_objects:
            obj.select_set(True)

        return True
