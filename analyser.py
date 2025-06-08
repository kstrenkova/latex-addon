# ---------------------------------------------------------------------------
# File name   : analyser.py
# Created By  : Katarina Strenkova
# ---------------------------------------------------------------------------

import bpy
import os.path

# functions from generator
from .generator import *
from .ll_table import *
from .characters_db import space_sizes, special_chars


# class for tokens
class Token:
    def __init__(self, token_type, token_value):
        self.type = token_type
        self.value = token_value


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
    def __init__(self, ei_array, exp_ix, frac, matrix):
        self.ei_array = ei_array
        self.exp_ix = exp_ix
        self.frac = frac
        self.matrix = matrix
        
        
# class fot sum        
class Sum:
    def __init__(self, bool, name, up_collection, down_collection, array):
        self.bool = bool
        self.name = name
        self.up_collection = up_collection 
        self.down_collection = down_collection
        self.array = array


# class for fraction
class FractionState:
    def __init__(self, parent_coll, init_params):
        self.parent_coll = parent_coll
        self.init_params = init_params
        self.ncoll = None
        self.dcoll = None
        self.nwidth = 0
        self.dwidth = 0
        
        
# class for matrix        
class Matrix:
    def __init__(self, obj_array, row_num):
        self.obj_array = obj_array
        self.row_num = row_num


# class for lexical analyser
class LexicalAnalyser:
    def __init__(self, latex_text):
        self.text = latex_text
        self.position = 0

    # function gets the next token
    def get_token(self):
        state = "STATE_START"
        string_value = ""

        while self.position < len(self.text):
            c = self.text[self.position]
            c_type = self.get_char(self.text[self.position])

            # choose the next state
            if state == "STATE_START":
                if c_type == "BACKSLASH":
                    state = "STATE_COMMAND"
                    self.position += 1

                    # special case for space, e.g. a \ b
                    if self.position < len(self.text) and self.text[self.position] == ' ':
                        self.position += 1
                        return Token("_SPACE_COMMAND", ' ')

                    continue

                elif c_type == "WHITESPACE":
                    self.position += 1
                    continue

                elif c_type == "OTHER":
                    state = "STATE_TEXT"
                    string_value += c
                    self.position += 1
                    continue

                else:
                    self.position += 1
                    return Token(c_type, c)

            # COMMANDS
            elif state == "STATE_COMMAND":
                if c_type in special_chars:
                    self.position += 1
                    return Token("SPECIAL_CHAR", c)
                elif c_type == "BACKSLASH":
                    self.position += 1
                    return Token("ENTER", "\\")
                elif c_type == "OTHER" and c in space_sizes:
                    self.position += 1
                    return Token("_SPACE_COMMAND", c)
                elif c_type == "OTHER":
                    state = "STATE_COMMAND_NAME"
                else:
                    self.position += 1
                    return Token(c_type, c)

            # COMMAND NAME
            elif state == "STATE_COMMAND_NAME":
                if c_type == "OTHER" and c.isalpha():
                    string_value += c
                    self.position += 1
                else:
                    if string_value in space_sizes:
                        return Token("_SPACE_COMMAND", string_value)
                    else:
                        return Token("COMMAND", string_value)

            # TEXT
            elif state == "STATE_TEXT":
                if c_type != "OTHER":
                    return Token("_TEXT", string_value)
                else:
                    string_value += c
                    self.position += 1

        # TODO
        # characters in buffer
        if string_value != "":
            if state == "STATE_COMMAND":
                if string_value in space_sizes:
                    return Token("_SPACE_COMMAND", string_value)
                else:
                    return Token("COMMAND", string_value)
            elif state == "STATE_TEXT":
                return Token("_TEXT", string_value)
        
        # end token
        return Token("END", "")
                   
    # end of get_token()

    @staticmethod
    # function gets the current character
    def get_char(input_character):
        
        all_char = [
            ('\\', "BACKSLASH"),
            ('{', "OPEN_BRACKET"),
            ('}', "CLOSE_BRACKET"),
            ('^', "CARET"),
            ('_', "UNDERSCORE"),
            ('&', "AMPERSAND"),
            ('[', "ANGLE_BRACKETS"),
            (']', "ANGLE_BRACKETS"),
            (' ', "WHITESPACE"),
            ('\n', "WHITESPACE")
        ]
        
         # return input character
        for item in all_char:
            if input_character == item[0]:
                return item[1]
 
        return "OTHER"

    # function returns token to latex string
    def return_token(self, token):
        self.position -= len(token.value)

        # check if the token had a backslash before
        if self.position > 0:
            c = self.text[self.position - 1]
            if c == '\\':
                self.position -= 1

        # TODO
        # print(f"DEBUG: Returned token ('{token.type}', '{token.value}'). New position is {self.position}.")


class SyntaxAnalyser(LexicalAnalyser):
    def __init__(self, latex_text, context, text_scale, font_path):
        super().__init__(latex_text)

        self.stack = ['$', 'PROG']
        self.state_stack = []
        self.parsing_context = "DEFAULT"

        self.context = context
        self.text_scale = text_scale
        self.font_path = font_path
        self.font = []  # default_font, unicode_font
        self.sqrt = False
        self.sum = Sum(False, "", "", "", [])
        self.base_collection = ""
        self.current_collection = ""
        self.parameters = Parameters(text_scale, 0.0, 0.0, 0.0)
        self.levels = Levels([], False, 0, False)
        self.matrix = Matrix([[]], 0)
    
    # function returns if sequence of tokens is a matrix figure
    # { text }
    def is_matrix_figure(self, mode, parent_coll, xy_size):
        # {
        token = self.get_token()
        if token.type == "OPEN_BRACKET":
            # text
            all_matrix = [
                "bmatrix", "Bmatrix", "matrix", "pmatrix", "Pmatrix", "vmatrix", "Vmatrix"
            ]
            token = self.get_token()
            if token.type == "_TEXT" and token.value in all_matrix:
                # gets the bracket symbol
                bracket_type = self.get_mx_brackets(token.value)
                # }
                token = self.get_token()
                if token.type == "CLOSE_BRACKET":
                         
                    # at the end of matrix
                    if mode == "end":
                        # position matrix
                        gen_matrix_pos(self.context, self.matrix.obj_array, self.parameters)
                        
                        # get matrix parameters
                        xy_size = gen_matrix_param(self.context, self.parameters, parent_coll, xy_size)
                        
                        if not bracket_type[0] == '':
                            # generate left bracket of matrix
                            gen_text(self.context, bracket_type[0], self.font[1])
                            gen_brackets(self.context, self.parameters, parent_coll, self.base_collection, xy_size, True)
                            xy_size = gen_matrix_param(self.context, self.parameters, parent_coll, xy_size)
                            
                            # generate right bracket of matrix
                            gen_text(self.context, bracket_type[1], self.font[1])
                            gen_brackets(self.context, self.parameters, parent_coll, self.base_collection, xy_size, False)
                        
                        # center matrix into row
                        gen_matrix_center(self.parameters, parent_coll, xy_size, bracket_type[0])
                        
                        # clear matrix array
                        self.parameters.line = 0.0
                        self.matrix.obj_array = [[]]
                        self.matrix.row_num = 0
                    
                    return True
                else:
                    print("Error, missing closing bracket to command!")

        return False

    # <MATRIX> -> <CONST> <MATRIX>
    #          -> <BLOCK> <MATRIX>
    #          -> <COMMAND> <MATRIX>
    #          -> & <MATRIX>
    #          -> epsilon
    def sa_matrix(self, tmp_param, parent_coll):
        token = self.get_token()

        if self.is_const(token) or self.is_block(token) or self.is_command(token) or token.type == "AMPERSAND":
            # <CONST>
            if self.is_const(token):
                # enter (\\)
                if token.type == "ENTER":
                    # matrix cell collection
                    self.current_collection = gen_new_collection(self.context, "MatrixCellCollection", parent_coll)
                    
                    # add new array that represents row
                    self.matrix.obj_array.append([])
                    self.matrix.row_num += 1
                    self.matrix.obj_array[self.matrix.row_num].append(self.current_collection)
                    
                    # set width to start and height lower
                    self.parameters.width = tmp_param.width
                    self.parameters.line -= 1.0 * self.text_scale
                      
                self.return_token(token)  # return token
            
                if self.sa_const():  
                    # <MATRIX>
                    if self.sa_matrix(tmp_param, parent_coll):
                        return True

            # <BLOCK>
            elif self.is_block(token):
                self.return_token(token)
                if self.sa_block():
                    # <MATRIX>
                    if self.sa_matrix(tmp_param, parent_coll):
                        return True

            # <COMMAND>
            elif self.is_command(token):
                self.return_token(token)
                if self.sa_command():
                    # <MATRIX>
                    if self.sa_matrix(tmp_param, parent_coll):
                        return True

            # &
            elif token.type == "AMPERSAND":
                # matrix cell collection
                self.current_collection = gen_new_collection(self.context, "MatrixCellCollection", parent_coll)
                
                # add collection to row
                self.matrix.obj_array[self.matrix.row_num].append(self.current_collection)
                if self.sa_matrix(tmp_param, parent_coll):
                    # <MATRIX>
                    return True  

        else:
            # epsilon
            self.return_token(token)
            return True

        return False

    # <SQRT> -> [ <MORE_TERM> ] { <MORE_TERM> }
    #        -> { <MORE_TERM> }
    def sa_sqrt(self, mode):
        
        self.sqrt = True  # inside sqrt
        token = self.get_token()

        # [
        if token.type == "_TEXT" and token.value == "[":
            # creating square root multipliers
            self.levels.ei_array.append("exp")
            self.parameters.width += 0.1  # space before multipliers
            
            # <MORE_TERM>
            if self.sa_more_term():
                # ]
                token = self.get_token()
                if token.type == "_TEXT" and token.value == "]":
                    self.sqrt = False
                    self.levels.ei_array.pop()
                    gen_calculate(self.parameters, self.text_scale, self.levels)
                    
                    # {
                    token = self.get_token()
                    if token.type == "OPEN_BRACKET":
                        self.return_token(token)
                        # { <MORE_TERM> }
                        return self.sa_sqrt("multiple")

        # {
        elif token.type == "OPEN_BRACKET":
            # saving parameters
            gen_calculate(self.parameters, self.text_scale, self.levels)
            tmp_param = self.parameters.create_copy()
            
            # saving parent collection to bind children collections to
            parent_coll = self.current_collection
            
            sqrt_width = 0.855927586555481  # width of square root symbol
            
            # mode 'single' doesn't have multipliers
            if mode == "single":
                self.parameters.width += sqrt_width * self.parameters.scale
            else:    
                tmp_param.width -= (sqrt_width - 0.4) * self.parameters.scale
                self.parameters.width += 0.4 * self.parameters.scale
            
            # square root collection
            sqrt_coll = bpy.data.collections.new("SqrtCollection")
            bpy.data.collections[parent_coll].children.link(sqrt_coll)
            self.current_collection = sqrt_coll.name
            
            # <MORE_TERM>
            if self.sa_more_term():
                # }
                token = self.get_token()
                if token.type == "CLOSE_BRACKET":
                    # bool to determine moving of sqrt symbol
                    use_param = False
                    sqrt_param = {
                        "x_pos": 0,
                        "y_min": 0,
                        "y_max": 0
                    }

                    # gets parameters of text under square root
                    if len(bpy.data.collections[self.current_collection].all_objects): 
                        use_param = True
                        sqrt_param['x_pos'] = gen_group_width(self.context, self.current_collection)
                        sqrt_param['y_min'] = gen_min_y(self.context, self.current_collection)
                        sqrt_param['y_max'] = gen_group_height(self.context, self.current_collection)   
                    
                    # generating sqrt symbol
                    gen_sqrt_sym(self.context)
                    gen_collection(self.context, parent_coll, self.base_collection)  # symbol into collection
                    
                    # move sqrt symbol
                    gen_sqrt_move(self.context, tmp_param, sqrt_param, use_param)
                    
                    # join collection into parent collection
                    gen_join_collections(self.context, sqrt_coll, parent_coll)
                    self.current_collection = parent_coll  # set current collection
                    
                    return True
                else:
                    print("Error, missing closing bracket to command!")

        return False
    
    # <SUM> -> index_exponent
    #       -> epsilon
    def sa_sum(self, symbol):

        # generate sum symbol
        if not gen_math_sym(self.context, symbol, self.font[1]):
            return False
                    
        gen_calculate(self.parameters, self.text_scale, self.levels)
        self.parameters.height -= 0.4 * self.parameters.scale  # move lower
        gen_position(self.parameters, True)        
        gen_collection(self.context, self.current_collection, self.base_collection)
        
        self.sum.name = self.context.active_object.name  # save sum object
        token = self.get_token()  # get next token
        
        # check index or exponent for sum
        if token.type == "UNDERSCORE" or token.type == "CARET":
            self.return_token(token)
            self.sum.bool = True  # index and exponent for sum
            
            # saving parent collection to bind children collections to
            parent_coll = self.current_collection
            
            # collection for upper indexes
            up_coll = bpy.data.collections.new("SumUpCollection")
            bpy.data.collections[parent_coll].children.link(up_coll)
            self.sum.up_collection = up_coll.name

            # collection for upper indexes
            down_coll = bpy.data.collections.new("SumDownCollection")
            bpy.data.collections[parent_coll].children.link(down_coll)
            self.sum.down_collection = down_coll.name
            
            if token.type == "UNDERSCORE":
                self.current_collection = down_coll.name
            else:
                self.current_collection = up_coll.name    
            
            # index_exponent
            if self.sa_const():
                
                # move sum limits
                gen_move_sum(self.context, self.parameters, up_coll.name, self.sum)
                gen_move_sum(self.context, self.parameters, down_coll.name, self.sum)
                
                space = 0.1 * self.parameters.scale
                self.parameters.width = gen_fin_sum(self.context, self.sum, up_coll.name, down_coll.name) + space
                
                # join denominator collection into parent collection
                gen_join_collections(self.context, up_coll, parent_coll)
                gen_join_collections(self.context, down_coll, parent_coll)
                self.current_collection = parent_coll  # set current collection
                
                # clear variables for sum
                self.sum.bool = False 
                self.sum.array = []
                return True
        else:
            # epsilon
            self.return_token(token) 
            return True
    
    # function finds the wrong use of exponents and indexes
    #          generates index + exponent
    def is_both_ei(self, mode, brackets, saved_width, parent_coll, exp_ix_coll):
        
        token = self.get_token()  # get next token

        # multiple uses of exponent + index
        if self.levels.exp_ix and (token.type == "UNDERSCORE" or token.type == "CARET"):
            print("Error, use of both index and exponent is only permitted once!")
            return False
                    
        # exponent + index
        elif (mode == "CARET" and token.type == "UNDERSCORE") \
            or (mode == "UNDERSCORE" and token.type == "CARET"):
            
            self.return_token(token)
            self.levels.exp_ix = True  # is inside cyclus
            
            # special sum exponent or index
            if self.sum.bool:
                if token.type == "UNDERSCORE":
                    self.current_collection = self.sum.down_collection
                else:
                    self.current_collection = self.sum.up_collection
                    
            # move when its not already moved
            if not brackets:
                gen_calculate(self.parameters, self.text_scale, self.levels)
                gen_position(self.parameters, False)
            self.levels.ei_array.pop()
            
            # save first text width    
            first_width = gen_group_width(self.context, self.current_collection)
  
            if brackets:
                self.parameters.width = saved_width
            
            # call const function
            if not self.sa_const():
                return False
            
            self.levels.exp_ix = False  # is out of cyclus
            
            # calculate final width
            sec_width = gen_group_width(self.context, self.current_collection)
            fin_width = max(first_width, sec_width)    
            
            self.parameters.width = fin_width + 0.1 * self.parameters.scale
            
        elif token.type == "UNDERSCORE" or token.type == "CARET":
            print("Error, use brackets to correctly make multiple exponents or indexes!")
            return False
        
        else:
            self.return_token(token) 
            # move when its not already moved
            if not brackets:
                gen_calculate(self.parameters, self.text_scale, self.levels)
                gen_position(self.parameters, not self.levels.exp_ix)
            self.levels.ei_array.pop()
                
        # join collection into parent collection
        gen_join_collections(self.context, exp_ix_coll, parent_coll)
        self.current_collection = parent_coll  # set current collection
            
        return True    
        

    # <AFTER_EI> -> { <MORE_TERM> }
    #            -> text
    #            -> special_symbols
    #            -> command (special group of commands)
    def sa_after_ei(self, mode):
        # saving parent collection to bind children collections to
        parent_coll = self.current_collection
        
        # exponent or index collection
        exp_ix_coll = bpy.data.collections.new("ExponentIndexCollection")
              
        bpy.data.collections[parent_coll].children.link(exp_ix_coll)
        self.current_collection = exp_ix_coll.name
        
        # {
        token = self.get_token()
        if token.type == "OPEN_BRACKET":
            tmp_width = self.parameters.width
            # <MORE_TERM>
            if self.sa_more_term():
                # }
                token = self.get_token()
                if token.type == "CLOSE_BRACKET":
                    return self.is_both_ei(mode, True, tmp_width, parent_coll, exp_ix_coll)
                else:
                    print("Error, missing closing bracket to command!")

        # text
        # special_symbols
        elif token.type == "_TEXT" or token.type == "_SPECIAL_CHAR":
            # generate text
            gen_text(self.context, token.value, self.font[0])
            gen_collection(self.context, self.current_collection, self.base_collection)
        
            return self.is_both_ei(mode, False, self.parameters.width, parent_coll, exp_ix_coll)
        
        # command (special group of commands)
        elif token.type == "COMMAND":
            # generate mathematic symbol
            gen_math_sym(self.context, token.value,  self.font[1])
            gen_collection(self.context, self.current_collection, self.base_collection)   
        
            return self.is_both_ei(mode, False, self.parameters.width, parent_coll, exp_ix_coll)
        
        return False

    # <CONST> -> text
    #         -> special_symbols
    #         -> enter
    #         -> index_exponent <IN_BRACKETS>
    def sa_const(self):
        token = self.get_token()

        # text + special_symbols
        if token.type == "_TEXT" or token.type == "_SPECIAL_CHAR":
            gen_text(self.context, token.value, self.font[0])
            gen_calculate(self.parameters, self.text_scale, self.levels)
            gen_position(self.parameters, True)
            gen_collection(self.context, self.current_collection, self.base_collection)
            
            return True
        
        # enter
        elif token.type == "ENTER":
            # skip if not in matrix
            return True

        # index_exponent
        elif token.type == "UNDERSCORE":
            self.levels.ei_array.append("ix")
            gen_calculate(self.parameters, self.text_scale, self.levels)
            # <IN_BRACKETS>
            if self.sa_after_ei("UNDERSCORE"):
                return True

        elif token.type == "CARET":
            self.levels.ei_array.append("exp")
            gen_calculate(self.parameters, self.text_scale, self.levels)
            # <IN_BRACKETS>
            if self.sa_after_ei("CARET"):
                return True

        return False

    # <COMMAND> -> { <MORE_TERM> }
    #           -> sqrt <SQRT>
    #           -> frac <FRAC>
    #           -> command <COMM_ARG>
    def sa_command(self):
        # {
        token = self.get_token()
        if token.type == "OPEN_BRACKET":
            # <MORE_TERM>
            if self.sa_more_term():
                # }
                token = self.get_token()
                if token.type == "CLOSE_BRACKET":
                    return True
                else:
                    print("Error, missing closing bracket to command")

        # COMMAND type
        elif token.type == "COMMAND":
            # sqrt
            if token.value == "sqrt":
                # <SQRT>
                if self.sa_sqrt("single"):
                    return True
            
            # frac
            elif token.value == "frac":
                # <FRAC>
                if self.sa_frac():
                    return True 
                
            # sum
            elif token.value == "sum" or token.value == "prod":
                 # <SUM>
                 if self.sa_sum(token.value):
                     return True                     

            # command
            else:
                # mathematic symbols
                if not gen_math_sym(self.context, token.value, self.font[1]):
                    return False
                
                gen_calculate(self.parameters, self.text_scale, self.levels)
                gen_position(self.parameters, True)
                
                # move prod and integral symbol
                if token.value == "int":
                    self.context.active_object.location.y -= 0.3 * self.parameters.scale   
                    self.parameters.width -= 0.2 * self.parameters.scale
                
                gen_collection(self.context, self.current_collection, self.base_collection)
                return True

        return False

    # <BLOCK> -> begin { text } <MATRIX> end { text }
    def sa_block(self):
        
        # begin
        token = self.get_token()
        if token.type == "COMMAND" and token.value == "begin":
            
            # saving parent collection to bind children collections to
            parent_coll = self.current_collection
            
            # saving current parameters
            gen_calculate(self.parameters, self.text_scale, self.levels)
            tmp_param = self.parameters.create_copy()
            
            xy_size = [tmp_param.width]  # array for matrix parameters
            
            # matrix collection
            mx_coll = bpy.data.collections.new("MatrixBodyCollection")
            bpy.data.collections[parent_coll].children.link(mx_coll)
            
            # first matrix cell collection
            self.current_collection = gen_new_collection(self.context, "MatrixCellCollection", mx_coll.name)
            self.matrix.obj_array[self.matrix.row_num].append(self.current_collection)
            
            # { text }
            if self.is_matrix_figure("begin", mx_coll.name, xy_size):
                # <MATRIX>
                if self.sa_matrix(tmp_param, mx_coll.name):
                    # end
                    token = self.get_token()
                    if token.type == "COMMAND" and token.value == "end":
                        # { text }
                        if self.is_matrix_figure("end", mx_coll.name, xy_size):
                            # set width of parameters
                            self.parameters.width = gen_group_width(self.context, mx_coll.name) + 0.25
                             
                            # link objects to matrix collection
                            for collection in bpy.data.collections:
                                if "MatrixCellCollection" in collection.name:
                                    # join all objects into one parent collection
                                    for obj in collection.all_objects:
                                        bpy.data.collections[mx_coll.name].objects.link(obj)
                                        collection.objects.unlink(obj)   
                            
                                    # remove matrix cell collection
                                    bpy.data.collections.remove(collection)
                               
                            # join matrix collection into parent collection
                            gen_join_collections(self.context, mx_coll, parent_coll)
                            self.current_collection = parent_coll  # set current collection
                            
                            return True
        # sa_block()                
        return False

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
        if action == '#ACTION_GENERATE_TEXT':
            token = self.get_token()
            gen_text(self.context, token.value, self.font[0])
            gen_calculate(self.parameters, self.text_scale, self.levels)
            gen_position(self.parameters, True)
            gen_collection(self.context, self.current_collection, self.base_collection)
            return True

        # <COMMAND> actions
        if action == '#ACTION_SPACE':
            token = self.get_token()
            space = space_sizes[token.value] * self.parameters.scale
            self.parameters.width += space
            return True

        elif action == '#ACTION_SUM':
            return self.sa_sum("sum")

        elif action == '#ACTION_PROD':
            return self.sa_sum("prod")

        elif action == '#ACTION_INTEGRAL':
            gen_calculate(self.parameters, self.text_scale, self.levels)
            gen_position(self.parameters, True)

            # move prod and integral symbol
            self.context.active_object.location.y -= 0.3 * self.parameters.scale
            self.parameters.width -= 0.2 * self.parameters.scale
            gen_collection(self.context, self.current_collection, self.base_collection)
            return True

        elif action == '#ACTION_MATH_SYMBOL':
            if not gen_math_sym(self.context, token.value, self.font[1]):
                return False
            gen_calculate(self.parameters, self.text_scale, self.levels)
            gen_position(self.parameters, True)
            gen_collection(self.context, self.current_collection, self.base_collection)
            return True

        # <SQRT> actions
        elif action == '#ACTION_SQRT_INIT':
            # saving parameters
            gen_calculate(self.parameters, self.text_scale, self.levels)
            self.state_stack.append(self.parameters.create_copy())
            self.state_stack.append(self.current_collection)
            print(f"STATE STACK: {self.state_stack}")

            sqrt_width = 0.855927586555481  # width of square root symbol

            # mode 'single' doesn't have multipliers
            #if mode == "single":
            self.parameters.width += sqrt_width * self.parameters.scale
            # else:
            #     tmp_param.width -= (sqrt_width - 0.4) * self.parameters.scale
            #     self.parameters.width += 0.4 * self.parameters.scale

            # square root collection
            sqrt_collection = bpy.data.collections.new("SqrtCollection")
            bpy.data.collections[self.current_collection].children.link(sqrt_collection)
            self.state_stack.append(sqrt_collection)
            self.current_collection = sqrt_collection.name
            print(f"STATE STACK: {self.state_stack}")
            return True

        elif action == '#ACTION_SQRT_CREATE':
            print(f"STATE STACK: {self.state_stack}")
            sqrt_collection = self.state_stack.pop()
            parent_coll = self.state_stack.pop()
            copied_param = self.state_stack.pop()

            use_param = False
            sqrt_param = {
                "x_pos": 0,
                "y_min": 0,
                "y_max": 0
            }

            # gets parameters of text under square root
            if len(sqrt_collection.all_objects):
                use_param = True
                sqrt_param['x_pos'] = gen_group_width(self.context, self.current_collection)
                sqrt_param['y_min'] = gen_min_y(self.context, self.current_collection)
                sqrt_param['y_max'] = gen_group_height(self.context, self.current_collection)

            # generating sqrt symbol
            gen_sqrt_sym(self.context)
            gen_collection(self.context, parent_coll, self.base_collection)  # symbol into collection

            # move sqrt symbol
            gen_sqrt_move(self.context, copied_param, sqrt_param, use_param)

            # join collection into parent collection
            gen_join_collections(self.context, sqrt_collection, parent_coll)
            self.current_collection = parent_coll  # set current collection
            return True

        # <FRAC> actions
        elif action == '#ACTION_FRAC_INIT':
            # increasing level of fraction
            self.levels.frac += 1
            self.parameters.width += 0.1 * self.parameters.scale  # space before fraction

            gen_calculate(self.parameters, self.text_scale, self.levels)

            parent_coll = bpy.data.collections[self.current_collection]
            fs = FractionState(parent_coll, self.parameters.create_copy())

            # numerator collection
            ncoll = bpy.data.collections.new("NumeratorCollection")
            bpy.data.collections[self.current_collection].children.link(ncoll)
            fs.ncoll = ncoll

            self.state_stack.append(fs)

            self.current_collection = ncoll.name
            return True

        elif action == '#ACTION_FRAC_UP':
            fs = self.state_stack[-1]

            # gets the furthest x position
            if len(bpy.data.collections[self.current_collection].all_objects):
                fs.nwidth = gen_group_width(self.context, self.current_collection)

            # move numerator objects
            gen_calculate(self.parameters, self.text_scale, self.levels)
            gen_frac_num(self.context, self.parameters, fs.ncoll.name)

            # denominator collection
            dcoll = bpy.data.collections.new("DenominatorCollection")
            fs.parent_coll.children.link(dcoll)
            fs.dcoll = dcoll

            self.current_collection = dcoll.name

            # reloading last width
            self.parameters.width = fs.init_params.width
            return True

        elif action == '#ACTION_FRAC_DOWN':
            fs = self.state_stack.pop()

            # gets the furthest x position
            if len(bpy.data.collections[self.current_collection].all_objects):
                fs.dwidth = gen_group_width(self.context, self.current_collection)

            # move denominator objects
            gen_calculate(self.parameters, self.text_scale, self.levels)
            gen_frac_den(self.context, self.parameters, fs.dcoll.name)

            # finding longer text width
            if fs.dwidth > fs.nwidth:
                line_length = fs.dwidth
                center_coll = fs.ncoll.name
            else:
                line_length = fs.nwidth
                center_coll = fs.dcoll.name

            # generating fraction line
            gen_frac_line(self.context, fs.init_params, line_length)

            # center numerator and denominator
            gen_center(self.context, fs.nwidth, fs.dwidth, center_coll)
            gen_collection(self.context, fs.dcoll.name, self.base_collection)

            # join numerator and denominator collections
            gen_join_collections(self.context, fs.dcoll, fs.ncoll.name)

            # join denominator collection into parent collection
            gen_join_collections(self.context, fs.ncoll, fs.parent_coll.name)
            self.current_collection = fs.parent_coll  # set current collection

            # set back line width
            self.parameters.width = line_length + 0.2 * self.parameters.scale  # space

            # decreasing level of fraction
            self.levels.frac -= 1
            return True

        else:
            print(f"Unknown action: '{action}'")
            return False

    # main function for parsing process
    def parse(self):
        try:
            # creating base collection
            collection = bpy.data.collections.new("MathematicalEqCollection")
            bpy.context.scene.collection.children.link(collection)

            # set active collection
            layer_collection = bpy.context.view_layer.layer_collection
            for layer in layer_collection.children:
                if layer.name == collection.name:
                    bpy.context.view_layer.active_layer_collection = layer

            self.base_collection = collection.name
            self.current_collection = collection.name

            # chosen default font
            if self.font_path != "":
                self.font.append(bpy.data.fonts.load(self.font_path))

            # unicode font for mathematical symbols (simplified path handling)
            font_file = os.path.join(os.path.dirname(__file__), "fonts", "Kelvinch-Roman.otf")
            self.font.append(bpy.data.fonts.load(font_file))

        except Exception as e:
            print(f"Error during initialization: {e}")
            return False

        parsing_success = True

        # parsing loop
        while self.stack:
            top_of_stack = self.stack[-1]
            token = self.peek_token()
            print(f"STACK: {self.stack}")

            # successful parsing
            if top_of_stack == '$' and token.type == 'END':
                print("Success!")
                self.stack.pop()
                break

            # actions
            elif top_of_stack.startswith('#'):
                action = self.stack.pop()
                print(f"CT {token.value}")
                if not self.execute_action(action, token):
                    print(f"Action error: {action}")
                    return False

            # terminal
            elif self.is_terminal(top_of_stack):
                if top_of_stack == token.value:
                    self.stack.pop()
                    self.get_token()
                else:
                    print(f"Syntax Error: Expected '{top_of_stack}' but got '{token.value}'")
                    parsing_success = False
                    break

            # non-terminal
            else:
                print(f"Token type: '{token.type}'")
                print(f"Token value: '{token.value}'")
                # TODO clean lookup
                # TODO ANGLE_BRACKETS OUTSIDE OF SQRT
                lookup_key = token.value if token.type == "COMMAND" or token.type == "CLOSE_BRACKET" or token.type == "OPEN_BRACKET" else token.type
                if self.parsing_context == "SQRT" and token.type == "ANGLE_BRACKETS" and token.value in ['[',']']:
                    lookup_key = token.value
                if token.type == "_SPACE_COMMAND":
                    lookup_key = token.type
                rule_rhs = math_ll_table.get((top_of_stack, lookup_key))

                if rule_rhs:
                    self.stack.pop()
                    if rule_rhs != ['epsilon']:
                        for symbol in reversed(rule_rhs):
                            self.stack.append(symbol)
                else:
                    print(f"Syntax Error: No rule for ({top_of_stack}, {lookup_key}, {rule_rhs})")
                    parsing_success = False
                    break

        if not parsing_success or self.stack:
            print("Error, not all tokens have been read!")
            return False

        # select all objects in base collection
        for obj in bpy.data.collections[collection.name].all_objects:
            obj.select_set(True)

        return True

    def is_terminal(self, symbol):
        return not (symbol.isupper() and symbol != '$')

    def peek_token(self):
        token = self.get_token()
        self.return_token(token)
        return token
