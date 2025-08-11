# ---------------------------------------------------------------------------
# File name   : lexical_analyser.py
# Created By  : Katarina Strenkova
# ---------------------------------------------------------------------------

# TODO remove ..data
from ..data.characters_db import *


# class for tokens
class Token:
    def __init__(self, token_type, token_value):
        self.type = token_type
        self.value = token_value


# class for lexical analyser
class LexicalAnalyser:
    def __init__(self, latex_text, position):
        self.text = latex_text
        self.position = position
        print(f"Lexer created for text: '{self.text[:20]}...' at position {self.position}")

    # function gets the next token
    def get_token(self):
        state = "STATE_START"
        string_value = ""

        while self.position < len(self.text):
            c = self.text[self.position]
            c_type = char_type.get(c, "OTHER")

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
                    return Token("_ENTER", "\\")
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

    # function returns token to latex string
    def return_token(self, token):
        self.position -= len(token.value)

        # check if the token had a backslash before
        if self.position > 0:
            c = self.text[self.position - 1]
            if c == '\\':
                self.position -= 1

    # function checks the next token
    def peek_token(self):
        token = self.get_token()
        self.return_token(token)
        return token
