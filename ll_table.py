# ---------------------------------------------------------------------------
# File name   : ll_table.py
# Created By  : Katarina Strenkova
# ---------------------------------------------------------------------------

math_ll_table = {
    # --- PROG ---
    # <PROG> -> <TERM> <MORE_TERM>
    ('PROG', '_TEXT'):            ['TERM', 'MORE_TERM'],
    ('PROG', '_SPECIAL_CHAR'):    ['TERM', 'MORE_TERM'],
    ('PROG', 'enter'):            ['TERM', 'MORE_TERM'],
    ('PROG', 'index_exponent'):   ['TERM', 'MORE_TERM'],
    ('PROG', '{'):                ['TERM', 'MORE_TERM'],
    ('PROG', 'sqrt'):             ['TERM', 'MORE_TERM'],
    ('PROG', 'frac'):             ['TERM', 'MORE_TERM'],
    ('PROG', 'command'):          ['TERM', 'MORE_TERM'],
    ('PROG', 'begin'):            ['TERM', 'MORE_TERM'],

    # --- TERM ---
    # <TERM> -> <CONST>
    ('TERM', '_TEXT'):            ['CONST'],
    ('TERM', '_SPECIAL_CHAR'):    ['CONST'],
    ('TERM', '_ENTER'):           ['CONST'],
    ('TERM', '_UNDERSCORE'):      ['CONST'],
    ('TERM', '_CARET'):           ['CONST'],
    # <TERM> -> <COMMAND>
    ('TERM', '{'):                ['COMMAND'],
    ('TERM', 'sqrt'):             ['COMMAND'],
    ('TERM', 'frac'):             ['COMMAND'],
    ('TERM', 'command'):          ['COMMAND'],
    ('TERM', '_SPACE_COMMAND'):   ['COMMAND'],
    ('TERM', '_MATH_SYMBOL'):     ['COMMAND'],
    # <TERM -> <BLOCK>
    ('TERM', 'begin'):            ['BLOCK'],

    # --- MORE_TERM ---
    # <MORE_TERM> -> <TERM> <MORE_TERM>
    ('MORE_TERM', '_TEXT'):            ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_SPECIAL_CHAR'):    ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'enter'):            ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_UNDERSCORE'):      ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_CARET'):           ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '{'):                ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'sqrt'):             ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'frac'):             ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'command'):          ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_SPACE_COMMAND'):   ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_MATH_SYMBOL'):     ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'begin'):            ['TERM', 'MORE_TERM'],
    # <MORE_TERM> -> epsilon
    ('MORE_TERM', '}'):                ['epsilon'],
    ('MORE_TERM', ']'):                ['epsilon'],
    ('MORE_TERM', '$'):                ['epsilon'],
    ('MORE_TERM', 'END'):              ['epsilon'],

    # --- CONST ---
    # <CONST> -> text
    ('CONST', '_TEXT'):             ['#ACTION_GENERATE_TEXT'],
    # <CONST> -> special_char
    ('CONST', '_SPECIAL_CHAR'):     ['#ACTION_GENERATE_TEXT'],
    # <CONST> -> enter
    ('CONST', '_ENTER'):            ['enter'],
    # <CONST> -> index_exponent <AFTER_EI>
    # <CONST> -> index <AFTER_EI> <OPT_EXP>
    # <CONST> -> exponent <AFTER_EI> <OPT_IX>
    # <OPT_EXP> -> exponent <AFTER_EI>
    # <OPT_EXP> -> epsilon
    # <OPT_IX> -> index <AFTER_EI>
    # <OPT_IX> -> epsilon
    # <AFTER_EI> -> text
    # <AFTER_EI> -> special_symbols
    # <AFTER_EI> -> { <MORE_TERM> }
    # <AFTER_EI> -> <COMMAND>
    ('CONST', '_UNDERSCORE'): [
        '#ACTION_LEVEL_DOWN', '#ACTION_EI_INIT', 'AFTER_EI', '#ACTION_EI_BOTH',
    ],
    ('CONST', '_CARET'): [
        '#ACTION_LEVEL_UP', '#ACTION_EI_INIT', 'AFTER_EI', '#ACTION_EI_BOTH',
    ],


    # --- COMMAND ---
    # <COMMAND> -> { <MORE_TERM> }
    ('COMMAND', '{'):                ['{', 'MORE_TERM', '}'],
    # <COMMAND> -> sqrt <SQRT>
    ('COMMAND', 'sqrt'):             ['#ACTION_SQRT_CONTEXT', 'sqrt', 'SQRT', '#ACTION_RESET_CONTEXT',],
    # <COMMAND> -> frac <FRAC>
    ('COMMAND', 'frac'):             ['frac', 'FRAC'],
    # <COMMAND> -> command
    ('COMMAND', 'sum'):              ['sum', '#ACTION_SUM'],
    ('COMMAND', 'prod'):             ['prod', '#ACTION_PROD'],
    ('COMMAND', '_SPACE_COMMAND'):   ['#ACTION_SPACE'],
    ('COMMAND', '_MATH_SYMBOL'):     ['#ACTION_MATH_SYMBOL'],
    ('COMMAND', 'int'):              ['int', '#ACTION_INTEGRAL'],

    # --- BLOCK ---
    # <BLOCK> -> begin { text } <MATRIX> end { text }
    ('BLOCK', 'begin'): [
        'begin', '#ACTION_MATRIX_INIT', '{', 'matrix', '}',
        'MATRIX',
        'end', '#ACTION_MATRIX_CREATE', '{', 'matrix', '}'
    ],

    # --- AFTER_EI ---
    # <AFTER_EI> -> text
    ('AFTER_EI', '_TEXT'):           ['#ACTION_GENERATE_TEXT'],
    # <AFTER_EI> -> special_symbols
    ('AFTER_EI', '_SPECIAL_CHAR'):   ['#ACTION_GENERATE_TEXT'],
    # <AFTER_EI> -> { <MORE_TERM> }
    ('AFTER_EI', '{'):               ['COMMAND'],
    # <AFTER_EI> -> <COMMAND>
    ('AFTER_EI', 'sqrt'):            ['COMMAND'],
    ('AFTER_EI', 'frac'):            ['COMMAND'],
    ('AFTER_EI', '_MATH_SYMBOL'):    ['COMMAND'],

    # --- SQRT ---
    # <SQRT> -> [ <MORE_TERM> ] { <MORE_TERM> }
    ('SQRT', '['): [
        '[', 'MORE_TERM', ']',
        '{', '#ACTION_SQRT_INIT', 'MORE_TERM', '}', '#ACTION_SQRT_CREATE',
    ],
    # <SQRT> -> { <MORE_TERM> }
    ('SQRT', '{'): [ '{', '#ACTION_SQRT_INIT', 'MORE_TERM', '}', '#ACTION_SQRT_CREATE' ],

    # --- FRAC ---
    # <FRAC> -> { <MORE_TERM> } { <MORE_TERM> }
    ('FRAC', '{'): [
        '{', '#ACTION_FRAC_INIT', 'MORE_TERM', '}', '#ACTION_FRAC_UP',
        '{', 'MORE_TERM', '}', '#ACTION_FRAC_DOWN'
    ],

    # --- MATRIX ---
    # TODO
    ('MATRIX', '_TEXT'):            ['CONST', 'MATRIX'],
    ('MATRIX', '_SPECIAL_CHAR'):    ['CONST', 'MATRIX'],
    ('MATRIX', '_ENTER'):           ['#ACTION_MATRIX_NEW_ROW', 'MATRIX'],
    ('MATRIX', '{'):                ['COMMAND', 'MATRIX'],
    ('MATRIX', 'sqrt'):             ['COMMAND', 'MATRIX'],
    ('MATRIX', 'frac'):             ['COMMAND', 'MATRIX'],
    ('MATRIX', 'command'):          ['COMMAND', 'MATRIX'],
    ('MATRIX', '_AMPERSAND'):       ['#ACTION_MATRIX_NEW_CELL', 'MATRIX'],
    ('MATRIX', 'end'):              ['epsilon'],
}