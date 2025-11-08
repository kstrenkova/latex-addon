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

    # function that returns if the string is at the end
    def is_end(self):
        return self.position >= len(self.text)

    # function looks at the next character
    def get_char(self):
        return self.text[self.position]

    # function creates a text token
    def state_text(self):
        text = ""
        while not self.is_end() and self.get_char() not in char_type and not self.get_char().isspace():
            text += self.get_char()
            self.position += 1
        return Token("_TEXT", text)

    # function skips all the whitespace characters
    def state_whitespace(self):
        while not self.is_end() and self.get_char().isspace():
            self.position += 1

    # function creates a command token
    def state_command(self):
        c = self.get_char()
        c_type = char_type.get(c)

        if c_type == "BACKSLASH":
            self.position += 1
            return Token("_ENTER", c)
        elif c_type in special_chars:
            self.position += 1
            return Token("_SPECIAL_CHAR", c)
        elif c_type: # \[ \(
            self.position += 1
            c = '\\' + c
            return Token("COMMAND", c)
        elif c in space_sizes:
            self.position += 1
            return Token("_SPACE_COMMAND", c)

        name = ""
        while not self.is_end() and self.get_char().isalpha():
            name += self.get_char()
            self.position += 1

        if name in space_sizes:
            return Token("_SPACE_COMMAND", name)

        if name in unicode_chars:
            return Token("_MATH_SYMBOL", name)

        return Token("COMMAND", name)

    # function returns the next token
    def get_token(self):
        # <WHITESPACE>
        self.state_whitespace()

        if self.is_end():
            return Token("END", "")

        c = self.get_char()
        c_type = char_type.get(c)

        # <STATE_COMMAND>
        if c_type == "BACKSLASH":
            self.position += 1
            return self.state_command()

        # SPECIAL CHARACTERS
        if c_type:
            self.position += 1
            return Token(c_type, c)

        # <STATE_TEXT>
        return self.state_text()

    # function returns the position before the current token
    def return_token(self, token):
        self.position -= len(token.value)

        # check if the token had a backslash before
        if self.position > 0:
            c = self.text[self.position - 1]
            if c == '\\':
                self.position -= 1

    # function checks the value of the next token
    def peek_token(self):
        token = self.get_token()
        self.return_token(token)
        return token

    # function returns the full \verb command content
    def get_verb_content(self):
        content = []
        while not self.is_end():
            c = self.get_char()
            if c == '|':
                return ''.join(content), ""

            # skip new lines but leave spaces
            if c not in '\n\r':
                content.append(c)
            self.position += 1

        return "", "Missing | symbol in function \verb!"
