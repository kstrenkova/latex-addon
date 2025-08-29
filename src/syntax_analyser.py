# ---------------------------------------------------------------------------
# File name   : syntax_analyser.py
# Created By  : Katarina Strenkova
# ---------------------------------------------------------------------------

import bpy
import os.path

from .generator import *
from .syntax_analyser_math import MathSyntaxAnalyser
from .syntax_utils import Defaults, Parameters

# TODO get rid of ..data
from ..data.ll_table import *
from ..data.characters_db import *


# class for levels
class Levels:
    def __init__(self, ei_array, frac):
        self.ei_array = ei_array
        self.frac = frac
        self.sqrt = False


class SyntaxAnalyser:
    def __init__(self, lex, context, custom_prop):
        self.stack = ['$', 'PROG']
        self.state_stack = []

        self.lex = lex
        self.d = Defaults(context, custom_prop)
        self.parameters = Parameters(custom_prop.text_scale, 0.0, 0.0, 0.0)
        self.levels = Levels([], 0)
        self.block_type = ''

    def choose_rule(self, stack_top, token):
        # TODO clean lookup
        if token.type in {"COMMAND", "_CLOSE_CURLY", "_OPEN_CURLY"}:
            key = token.value
        else:
            key = token.type

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
            gen_text(token.value, self.d.font[0], self.d.current_coll)
            gen_calculate(self.parameters, self.d.text_scale, self.levels)
            gen_position(self.parameters, True)
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
        try:
            # creating base collection
            collection = bpy.data.collections.new("LatexCollection")
            bpy.context.scene.collection.children.link(collection)
            gen_activate_collection(collection.name)

            self.d.base_coll = collection.name
            self.d.current_coll = collection.name

            # chosen default font
            if self.d.font_path != "":
                self.d.font.append(bpy.data.fonts.load(self.d.font_path))

            # unicode font for mathematical symbols
            src_dir = os.path.dirname(__file__)
            font_file = os.path.join(os.path.dirname(src_dir), "data", "fonts", "Kelvinch-Roman.otf")
            self.d.font.append(bpy.data.fonts.load(font_file))

        except Exception as e:
            print(f"Error during initialization: {e}")
            return False

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
                terminal = token.value if token.type in ["COMMAND", "_OPEN_CURLY", "_CLOSE_CURLY"] else token.type

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
