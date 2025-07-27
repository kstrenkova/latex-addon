# ---------------------------------------------------------------------------
# File name   : syntax_analyser.py
# Created By  : Katarina Strenkova
# ---------------------------------------------------------------------------

import bpy
import os.path

from .generator import *
from .lexical_analyser import LexicalAnalyser
from .syntax_analyser_math import MathSyntaxAnalyser

# TODO get rid of ..data
from ..data.ll_table import *
from ..data.characters_db import *


# class that holds default settings
class Defaults:
    def __init__(self, context, custom_prop):
        self.context = context
        self.text_scale = custom_prop.text_scale
        self.font_path = custom_prop.font_path
        self.font = []  # default_font, unicode_font
        self.base_collection = ''
        self.current_collection = ''

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
    def __init__(self, ei_array, exp_ix, frac):
        self.ei_array = ei_array
        self.exp_ix = exp_ix
        self.frac = frac


class SyntaxAnalyser(LexicalAnalyser):
    def __init__(self, context, custom_prop):
        super().__init__(custom_prop.latex_text, 0)

        self.stack = ['$', 'PROG']
        self.state_stack = []
        self.parsing_context = "DEFAULT"

        self.cus_pt = custom_prop
        self.d = Defaults(context, custom_prop)
        self.parameters = Parameters(custom_prop.text_scale, 0.0, 0.0, 0.0)
        self.levels = Levels([], False, 0)

    def peek_token(self):
        token = self.get_token()
        self.return_token(token)
        return token

    def choose_rule(self, stack_top, token):
        # TODO clean lookup

        if token.type in {"COMMAND", "CLOSE_BRACKET", "OPEN_BRACKET"}:
            key = token.value
        else:
            key = token.type

        if stack_top == "PROG":
            key = "_ANY"

        print("KEY:", key)

        rule = ll_table.get((stack_top, key))
        return rule

    def execute_action(self, action, token):
        # <CONST> actions
        if action == '#ACTION_GENERATE_TEXT':
            token = self.get_token()
            gen_text(self.d.context, token.value, self.d.font[0])
            gen_calculate(self.parameters, self.d.text_scale, self.levels)
            gen_position(self.parameters, True)
            # gen_collection(self.d.current_collection, self.d.base_collection)
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
            gen_activate_collection(collection)

            self.d.base_collection = collection.name
            self.d.current_collection = collection.name

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
            token = self.peek_token()
            print(f"STACK: {self.stack}")
            print(f"TOKEN VALUE AND TYPE", token.value, token.type)

            # successful parsing
            if stack_top == '$' and token.type == 'END':
                print("Success!")
                self.stack.pop()
                break

            # TODO MATH MODE
            elif token.value == '$' and token.type == 'DOLLAR_SIGN':
                print("Entering math mode!")

                # call math syntax analyser
                math_syntax = MathSyntaxAnalyser(self.d.context, self.cus_pt, self.d.base_collection, self.get_position()+1) # TODO

                self.d.current_collection = gen_new_collection("MathematicalEqCollection", self.d.base_collection)

                # set active collection
                layer_collection = bpy.context.view_layer.layer_collection
                for layer in layer_collection.children:
                    print("Layer name: ", layer.name)
                    if layer.name == self.d.base_collection:
                        for l in layer.children:
                            print("Child Layer name: ", l.name, self.d.current_collection)
                            if l.name == self.d.current_collection.name:
                                bpy.context.view_layer.active_layer_collection = l
                                print(f"Active collection set to '{self.d.current_collection}'")

                status, position = math_syntax.parse()

                if not status:
                    warn_msg = 'Mathematical equation was not fully generated. Check system console for more info on this matter.'
                    # TODO PUT WARNING
                    print({'WARNING'}, warn_msg)
                    return False

                self.set_position(position)
                print("Returned from math mode!")

                # join collection into parent collection
                gen_join_collections(self.d.current_collection, self.d.base_collection)
                gen_activate_collection(collection)

            # actions
            elif stack_top.startswith('#'):
                action = self.stack.pop()
                print(f"CT {token.value}")
                if not self.execute_action(action, token):
                    print(f"Action error: {action}")
                    return False

            # terminal
            elif not (stack_top.isupper() and stack_top != '$'):
                if stack_top == token.value:
                    self.stack.pop()
                    self.get_token()
                else:
                    print(f"Syntax Error: Expected '{stack_top}' but got '{token.value}'")
                    return False

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
                    print(f"Syntax Error: No rule for ({stack_top}, {rule})")
                    return False

        if self.stack:
            print("Error, not all tokens have been read!")
            return False

        # select all objects in base collection
        for obj in bpy.data.collections[collection.name].all_objects:
            obj.select_set(True)

        return True
