# ---------------------------------------------------------------------------
# File name   : ll_table.py
# Created By  : Katarina Strenkova
# ---------------------------------------------------------------------------

ll_table = {
    # --- PROG ---
    # <PROG> -> <TERM> <MORE_TERM>
    ('PROG', '_ANY'):             ['TERM', 'MORE_TERM'],

    # --- TERM ---
    # <TERM> -> <CONST>
    ('TERM', '_TEXT'):            ['CONST'],

    # --- MORE_TERM ---
    # <MORE_TERM> -> <TERM> <MORE_TERM>
    ('MORE_TERM', '_TEXT'):            ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'DOLLAR_SIGN'):      ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'END'):              ['epsilon'],

    # --- CONST ---
    # <CONST> -> text
    ('CONST', '_TEXT'):             ['#ACTION_GENERATE_TEXT'],

    # <TERM> -> $ <MATH_INLINE_PROG> $
    # <TERM> -> \( <MATH_INLINE_PROG> \)
    # <TERM> -> begin { math } <MATH_INLINE_PROG> end { math }
    ('MATH_INLINE_PROG', '_ANY'):   ['MATH_INLINE_PROG']

    # <TERM> -> \[ <MATH_DISPLAY_PROG> \[
    # <TERM> -> begin { equation } <MATH_DISPLAY_PROG> end { equation }
    # <TERM> -> begin { displaymath } <MATH_DISPLAY_PROG> end { displaymath }
}

math_ll_table = {
    # --- PROG ---
    # <PROG> -> <TERM> <MORE_TERM>
    ('PROG', '_ANY'):             ['TERM', 'MORE_TERM'],

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
    ('TERM', 'sum'):              ['COMMAND'],
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
    ('MORE_TERM', 'sum'):              ['TERM', 'MORE_TERM'],
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
    # <CONST> -> index <EI_TERM> <EXP>
    ('CONST', '_UNDERSCORE'):       ['#ACTION_LEVEL_DOWN', '#ACTION_EI_INIT', 'EI_TERM', 'EXP'],
    # <CONST> -> exponent <EI_TERM> <IX>
    ('CONST', '_CARET'):            ['#ACTION_LEVEL_UP', '#ACTION_EI_INIT', 'EI_TERM', 'IX'],

    # <EXP> -> exponent <EI_TERM>
    # <EXP> -> epsilon
    ('EXP', '_CARET'):              ['#ACTION_EI_BOTH', '#ACTION_LEVEL_UP', 'EI_TERM', '#ACTION_EI_FINAL'],
    ('EXP', 'epsilon'):             ['#ACTION_EI_SINGLE'],

    # <IX> -> index <EI_TERM>
    # <IX> -> epsilon
    ('IX', '_UNDERSCORE'):          ['#ACTION_EI_BOTH', '#ACTION_LEVEL_DOWN', 'EI_TERM', '#ACTION_EI_FINAL'],
    ('IX', 'epsilon'):              ['#ACTION_EI_SINGLE'],

    # --- COMMAND ---
    # <COMMAND> -> { <MORE_TERM> }
    ('COMMAND', '{'):                ['{', 'MORE_TERM', '}'],
    # <COMMAND> -> sqrt <SQRT>
    ('COMMAND', 'sqrt'):             ['#ACTION_SQRT_CONTEXT', 'sqrt', 'SQRT', '#ACTION_RESET_CONTEXT',],
    # <COMMAND> -> frac <FRAC>
    ('COMMAND', 'frac'):             ['frac', 'FRAC'],
    # <COMMAND> -> command


    # <COMMAND> -> sum <SUM>
    # <SUM> -> index <EI_TERM>
    # <SUM> -> exponent <EI_TERM>
    # <SUM> ->
    ('SUM', '_UNDERSCORE'): [''],
    # <COMMAND> -> sum index <EI_TERM>
    # <COMMAND> -> sum exponent <EI_TERM>
    ('COMMAND', 'sum'):              ['sum', '#ACTION_SUM_INIT'],
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

    # --- EI_TERM ---
    # <EI_TERM> -> text
    ('EI_TERM', '_TEXT'):           ['#ACTION_GENERATE_TEXT'],
    # <EI_TERM> -> special_symbols
    ('EI_TERM', '_SPECIAL_CHAR'):   ['#ACTION_GENERATE_TEXT'],
    # <EI_TERM> -> { <MORE_TERM> }
    ('EI_TERM', '{'):               ['COMMAND'],
    # <EI_TERM> -> <COMMAND>
    ('EI_TERM', 'sqrt'):            ['COMMAND'],
    ('EI_TERM', 'frac'):            ['COMMAND'],
    ('EI_TERM', '_MATH_SYMBOL'):    ['COMMAND'],

    # --- SQRT ---
    # <SQRT> -> [ <MORE_TERM> ] { <MORE_TERM> }
    ('SQRT', '['): [
        '[', 'MORE_TERM', ']',
        '{', '#ACTION_SQRT_INIT', 'MORE_TERM', '}', '#ACTION_SQRT_CREATE',
    ],
    # <SQRT> -> { <MORE_TERM> }
    ('SQRT', '{'): ['{', '#ACTION_SQRT_INIT', 'MORE_TERM', '}', '#ACTION_SQRT_CREATE'],

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