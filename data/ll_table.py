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
    ('TERM', '_ENTER'):           ['CONST'],

    # <TERM> -> <COMMAND>
    ('TERM', 'textbf'):           ['COMMAND'],
    ('TERM', 'textit'):           ['COMMAND'],
    ('TERM', 'texttt'):           ['COMMAND'],

    # <TERM> -> <MATH_MODE>
    ('TERM', 'dollar'):           ['MATH_MODE'],
    ('TERM', '\('):               ['MATH_MODE'],
    ('TERM', '\['):               ['MATH_MODE'],

    # <MATH_MODE> -> $ <MATH_INLINE_PROG> $
    # <MATH_MODE> -> \( <MATH_INLINE_PROG> \)
    # <MATH_MODE> -> \[ <MATH_DISPLAY_PROG> \[
    ('MATH_MODE', 'dollar'):      ['#ACTION_MATH_INLINE_MODE', 'dollar'],
    ('MATH_MODE', '\('):          ['#ACTION_MATH_INLINE_MODE', '\)'],
    ('MATH_MODE', '\['):          ['#ACTION_MATH_DISPLAY_MODE', '\]'],

    # <TERM> -> $ <MATH_INLINE_PROG> $
    # <TERM> -> \( <MATH_INLINE_PROG> \)
    # <TERM> -> begin { math } <MATH_INLINE_PROG> end { math }

    # <TERM> -> \[ <MATH_DISPLAY_PROG> \[
    # <TERM> -> begin { equation } <MATH_DISPLAY_PROG> end { equation }
    # <TERM> -> begin { displaymath } <MATH_DISPLAY_PROG> end { displaymath }

    ('TERM', 'begin'):                 ['BLOCK'],

    # --- MORE_TERM ---
    # <MORE_TERM> -> <TERM> <MORE_TERM>
    ('MORE_TERM', '_TEXT'):            ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_ENTER'):           ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'textbf'):           ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'textit'):           ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'texttt'):           ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'begin'):            ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'dollar'):           ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '\('):               ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '\['):               ['TERM', 'MORE_TERM'],
    # <MORE_TERM> -> epsilon
    ('MORE_TERM', '}'):                ['epsilon'],
    ('MORE_TERM', 'item'):             ['epsilon'],
    ('MORE_TERM', 'end'):              ['epsilon'],
    ('MORE_TERM', 'END'):              ['epsilon'],

    # --- CONST ---
    # <CONST> -> text
    ('CONST', '_TEXT'):                ['#ACTION_GENERATE_TEXT'],
    ('CONST', '_ENTER'):               ['#ACTION_NEW_LINE'],

    # --- COMMAND ---
    # <COMMAND> -> change_font { MORE_TERM }
    ('COMMAND', 'textbf'):             ['textbf', '#ACTION_BOLD_TEXT', '{', 'MORE_TERM', '}', '#ACTION_BASE_TEXT'],
    ('COMMAND', 'textit'):             ['textit', '#ACTION_ITAL_TEXT', '{', 'MORE_TERM', '}', '#ACTION_BASE_TEXT'],
    ('COMMAND', 'texttt'):             ['texttt', '#ACTION_BOLD_TEXT'], # TODO

    # <BLOCK> -> begin { text } TODO end { text }

    # <BLOCK> -> begin { itemize } <ITEMIZE> end { itemize }
    # <ITEMIZE> -> item <ITEM>
    # <ITEMIZE> -> epsilon
    ('ITEMIZE', 'item'):         ['item', 'ITEM'],
    ('ITEMIZE', 'epsilon'):      ['#ACTION_NEW_LINE'],

    # <ITEM> -> [ <MORE_TERM> ] <MORE_TERM> <ITEMIZE>
    # <ITEM> -> <MORE_TERM> <ITEMIZE>
    ('ITEM', '['):               ['[', '#ACTION_SAVE_ITEM', ']', '#ACTION_ADD_ITEM', 'MORE_TERM', 'ITEMIZE'],
    # TODO other types
    ('ITEM', '_TEXT'):           ['#ACTION_ADD_ITEM', 'MORE_TERM', 'ITEMIZE'],

    # <ENUM> -> item <MORE_TERM> <ENUM>
    # <ENUM> -> epsilon
    ('ENUM', 'item'):            ['item', '#ACTION_ADD_ENUM', 'MORE_TERM', 'ENUM'],
    ('ENUM', 'epsilon'):         ['#ACTION_END_ENUM', '#ACTION_NEW_LINE'],

    # --- BLOCK ---
    # <BLOCK> -> begin { text } <BLOCK_CONTENT> end { text }
    ('BLOCK', 'begin'): [
        'begin', '{', '#ACTION_BLOCK_BEGIN', '}',
        # '#ACTION_BLOCK_INIT',
        # 'MORE_TERM',
        'ITEMIZE', # TODO temporary ITEMIZE, uncomment to print items
        # 'ENUM', # TODO temporary ENUM, uncomment to print numbered items
        'end', '{', '#ACTION_BLOCK_END', '}',
    ],
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
    ('TERM', '['):                ['CONST'],
    ('TERM', ']'):                ['CONST'],

    # <TERM> -> <COMMAND>
    ('TERM', '{'):                ['COMMAND'],
    ('TERM', 'sqrt'):             ['COMMAND'],
    ('TERM', 'frac'):             ['COMMAND'],
    ('TERM', 'sum'):              ['COMMAND'],
    ('TERM', 'prod'):             ['COMMAND'],
    ('TERM', 'int'):              ['COMMAND'],
    ('TERM', 'lim'):              ['COMMAND'],
    ('TERM', 'mathcal'):          ['COMMAND'],
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
    ('MORE_TERM', '['):                ['TERM', 'MORE_TERM'],
    ('MORE_TERM', ']'):                ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '{'):                ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'sqrt'):             ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'frac'):             ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'sum'):              ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'prod'):             ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'int'):              ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'lim'):              ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'mathcal'):          ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_SPACE_COMMAND'):   ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_MATH_SYMBOL'):     ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'begin'):            ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'dollar'):           ['TERM', 'MORE_TERM'],
    # <MORE_TERM> -> epsilon
    ('MORE_TERM', '}'):                ['epsilon'],
    ('MORE_TERM', '$'):                ['epsilon'],
    ('MORE_TERM', 'end'):              ['epsilon'],
    ('MORE_TERM', 'dollar'):           ['epsilon'],
    ('MORE_TERM', '\)'):               ['epsilon'],
    ('MORE_TERM', '\]'):               ['epsilon'],
    ('MORE_TERM', 'END'):              ['epsilon'],

    # --- CONST ---
    # <CONST> -> text
    ('CONST', '_TEXT'):                ['#ACTION_GENERATE_TEXT'],
    ('CONST', '['):                    ['#ACTION_GENERATE_TEXT'],
    ('CONST', ']'):                    ['#ACTION_GENERATE_TEXT'],
    # <CONST> -> special_char
    ('CONST', '_SPECIAL_CHAR'):        ['#ACTION_GENERATE_TEXT'],
    # <CONST> -> enter
    ('CONST', '_ENTER'):               ['enter'],
    # <CONST> -> index <EI_TERM> <EXP>
    ('CONST', '_UNDERSCORE'):          ['#ACTION_LEVEL_DOWN', '#ACTION_EI_INIT', 'EI_TERM', 'EXP'],
    # <CONST> -> exponent <EI_TERM> <IX>
    ('CONST', '_CARET'):               ['#ACTION_LEVEL_UP', '#ACTION_EI_INIT', 'EI_TERM', 'IX'],

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

    # <EXP> -> exponent <EI_TERM>
    # <EXP> -> epsilon
    ('EXP', '_CARET'):                 ['#ACTION_EI_BOTH', '#ACTION_LEVEL_UP', 'EI_TERM', '#ACTION_EI_FINAL'],
    ('EXP', 'epsilon'):                ['#ACTION_EI_SINGLE'],

    # <IX> -> index <EI_TERM>
    # <IX> -> epsilon
    ('IX', '_UNDERSCORE'):             ['#ACTION_EI_BOTH', '#ACTION_LEVEL_DOWN', 'EI_TERM', '#ACTION_EI_FINAL'],
    ('IX', 'epsilon'):                 ['#ACTION_EI_SINGLE'],

    # --- COMMAND ---
    # <COMMAND> -> { <MORE_TERM> }
    ('COMMAND', '{'):        ['{', 'MORE_TERM', '}'],
    # <COMMAND> -> sqrt <SQRT>
    ('COMMAND', 'sqrt'):     ['sqrt', 'SQRT'],
    # <COMMAND> -> frac <FRAC>
    ('COMMAND', 'frac'):     ['frac', 'FRAC'],

    # <COMMAND> -> RANGE_OPERATORS
    ('COMMAND', 'sum'):      ['#ACTION_RANGE_OP_INIT'],
    ('COMMAND', 'prod'):     ['#ACTION_RANGE_OP_INIT'],
    ('COMMAND', 'int'):      ['#ACTION_RANGE_OP_INIT'],
    ('COMMAND', 'lim'):      ['#ACTION_RANGE_OP_INIT'],

    # TODO rule: mathcal { LETTER }
    ('COMMAND', 'mathcal'):  ['mathcal', '{', '#ACTION_GENERATE_MATH_LETTER', '}'],

    # <COMMAND> -> space_commands
    ('COMMAND', '_SPACE_COMMAND'): ['#ACTION_SPACE'],
    ('COMMAND', '_MATH_SYMBOL'):   ['#ACTION_MATH_SYMBOL'],

    # --- BLOCK ---
    # <BLOCK> -> begin { text } <MATRIX> end { text }
    # TODO connect BLOCK from main syntax with MATRIX BLOCK
    ('BLOCK', 'begin'): [
        'begin', '{', '#ACTION_VALIDATE_MATRIX_TYPE', '}',
        '#ACTION_MATRIX_INIT',
        'MATRIX',
        '#ACTION_MATRIX_CREATE',
        'end', '{', '#ACTION_VALIDATE_MATRIX_TYPE', '}'
    ],

    # --- SQRT ---
    # <SQRT> -> [ <MORE_TERM> ] { <MORE_TERM> }
    ('SQRT', '['): [
        '[', '#ACTION_LEVEL_UP_SQRT', 'SQRT_CONTEXT', ']',
        '{', '#ACTION_SQRT_INIT_WITH_INDEX', 'MORE_TERM', '}',
        '#ACTION_SQRT_CREATE',
    ],
    # <SQRT> -> { <MORE_TERM> }
    ('SQRT', '{'): [
        '{', '#ACTION_SQRT_INIT', 'MORE_TERM', '}',
        '#ACTION_SQRT_CREATE',
    ],

    # TODO finish up sqrt context
    # --- SQRT_CONTEXT ---
    # <SQRT_CONTEXT> -> <TERM> <SQRT_CONTEXT>
    ('SQRT_CONTEXT', '_TEXT'):            ['TERM', 'SQRT_CONTEXT'],
    ('SQRT_CONTEXT', '_SPECIAL_CHAR'):    ['TERM', 'SQRT_CONTEXT'],
    # <SQRT_CONTEXT> -> epsilon
    ('SQRT_CONTEXT', ']'):             ['epsilon'],

    # --- FRAC ---
    # <FRAC> -> { <MORE_TERM> } { <MORE_TERM> }
    ('FRAC', '{'): [
        '{', '#ACTION_FRAC_INIT', 'MORE_TERM', '}', '#ACTION_FRAC_UP',
        '{', 'MORE_TERM', '}', '#ACTION_FRAC_DOWN'
    ],

    # --- MATRIX ---
    # <MATRIX> -> TODO
    # <MATRIX> -> enter <MATRIX>
    # <MATRIX> -> & <MATRIX>
    # <MATRIX> -> <CONST> <MATRIX>
    ('MATRIX', '_TEXT'):            ['CONST', 'MATRIX'],
    ('MATRIX', '_SPECIAL_CHAR'):    ['CONST', 'MATRIX'],
    ('MATRIX', '_ENTER'):           ['#ACTION_MATRIX_NEW_ROW', 'MATRIX'],
    ('MATRIX', '{'):                ['COMMAND', 'MATRIX'],
    ('MATRIX', 'sqrt'):             ['COMMAND', 'MATRIX'],
    ('MATRIX', 'frac'):             ['COMMAND', 'MATRIX'],
    ('MATRIX', '_AMPERSAND'):       ['#ACTION_MATRIX_NEW_CELL', 'MATRIX'],
    ('MATRIX', 'end'):              ['epsilon'],
}