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
    ('TERM', '_SPECIAL_CHAR'):    ['CONST'],
    ('TERM', '_PIPE'):            ['CONST'],
    ('TERM', '_OPEN_BRACKET'):    ['CONST'],
    ('TERM', '_CLOSE_BRACKET'):   ['CONST'],

    # <TERM> -> <COMMAND>
    ('TERM', '_OPEN_CURLY'):      ['COMMAND'],
    ('TERM', 'par'):              ['COMMAND'],
    ('TERM', 'textbf'):           ['COMMAND'],
    ('TERM', 'textit'):           ['COMMAND'],
    ('TERM', 'texttt'):           ['COMMAND'],
    ('TERM', 'verb'):             ['COMMAND'],

    # <TERM> -> <MATH_MODE>
    ('TERM', '_DOLLAR'):          ['MATH_MODE'],
    ('TERM', '\('):               ['MATH_MODE'],
    ('TERM', '\['):               ['MATH_MODE'],

    # <TERM> -> <BLOCK>
    ('TERM', 'begin'):            ['BLOCK'],

    # --- MORE_TERM ---
    # <MORE_TERM> -> <TERM> <MORE_TERM>
    ('MORE_TERM', '_TEXT'):            ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_ENTER'):           ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_SPECIAL_CHAR'):    ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_PIPE'):            ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_OPEN_CURLY'):      ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_OPEN_BRACKET'):    ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_CLOSE_BRACKET'):   ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'par'):              ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'textbf'):           ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'textit'):           ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'texttt'):           ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'verb'):             ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'begin'):            ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_DOLLAR'):          ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '\('):               ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '\['):               ['TERM', 'MORE_TERM'],
    # <MORE_TERM> -> epsilon
    ('MORE_TERM', '_CLOSE_CURLY'):     ['epsilon'],
    ('MORE_TERM', 'item'):             ['epsilon'],
    ('MORE_TERM', 'end'):              ['epsilon'],
    ('MORE_TERM', 'END'):              ['epsilon'],

    # --- CONST ---
    # <CONST> -> text
    ('CONST', '_TEXT'):                ['#ACTION_GENERATE_TEXT'],
    ('CONST', '_SPECIAL_CHAR'):        ['#ACTION_GENERATE_TEXT'],
    ('CONST', '_PIPE'):                ['#ACTION_GENERATE_TEXT'],
    ('CONST', '_OPEN_BRACKET'):        ['#ACTION_GENERATE_TEXT'],
    ('CONST', '_CLOSE_BRACKET'):       ['#ACTION_GENERATE_TEXT'],

    # <CONST> -> enter
    ('CONST', '_ENTER'):               ['\\', '#ACTION_NEW_LINE'],

    # --- COMMAND ---
    ('COMMAND', '_OPEN_CURLY'):        ['{', 'MORE_TERM', '}'],
    ('COMMAND', 'par'):                ['par', '#ACTION_PARAGRAPH'],

    # <COMMAND> -> change_font { MORE_TERM }
    ('COMMAND', 'textbf'):             ['textbf', '#ACTION_FONT_BOLD',     '{', 'MORE_TERM', '}', '#ACTION_FONT_BASE'],
    ('COMMAND', 'textit'):             ['textit', '#ACTION_FONT_ITALIC',   '{', 'MORE_TERM', '}', '#ACTION_FONT_BASE'],
    ('COMMAND', 'texttt'):             ['texttt', '#ACTION_FONT_TELETYPE', '{', 'MORE_TERM', '}', '#ACTION_FONT_BASE'],

    # <COMMAND> -> verb | <MORE_TERM> |
    ('COMMAND', 'verb'):               ['verb', '|', '#ACTION_GENERATE_VERB', '|'],

    # --- MATH_MODE ---
    # <MATH_MODE> -> $ <MATH_INLINE_PROG> $
    # <MATH_MODE> -> \( <MATH_INLINE_PROG> \)
    # <MATH_MODE> -> \[ <MATH_DISPLAY_PROG> \[
    ('MATH_MODE', '_DOLLAR'):          ['$',  '#ACTION_MATH_MODE_INLINE',  '$'],
    ('MATH_MODE', '\('):               ['\(', '#ACTION_MATH_MODE_INLINE',  '\)'],
    ('MATH_MODE', '\['):               ['\[', '#ACTION_MATH_MODE_DISPLAY', '\]'],

    # --- BLOCK ---
    # <BLOCK> -> begin { text } <BLOCK_CONTENT> end { text }
    ('BLOCK', 'begin'): [
        'begin', '{', '#ACTION_BLOCK_VERIFY_BEGIN', '}',
        '#ACTION_BLOCK_ENTER',
        'BLOCK_CONTENT',
        'end',   '{', '#ACTION_BLOCK_VERIFY_END',   '}',
    ],

    ('BLOCK_CONTENT', 'item'):         ['ITEMIZE'],
    ('BLOCK_CONTENT', '_OPEN_CURLY'):  ['{', 'ALIGN', '}', 'TABLE'], # TODO BETTER
    ('BLOCK_CONTENT', '_ANY'):         ['MORE_TERM'],
    ('BLOCK_CONTENT', 'begin'):        ['BLOCK'],  # TODO fix when begin is at the beginning
    ('BLOCK_CONTENT', 'end'):          ['epsilon'],

    # --- ITEMIZE ---
    # <ITEMIZE> -> item <ITEM>
    # <ITEMIZE> -> epsilon
    ('ITEMIZE', 'item'):         ['item', '#ACTION_NEW_LINE', 'ITEM'],
    ('ITEMIZE', 'epsilon'):      ['#ACTION_ITEM_END'],

    # <ITEM> -> [ <MORE_TERM> ] <MORE_TERM> <ITEMIZE>
    # <ITEM> -> <MORE_TERM> <ITEMIZE>
    ('ITEM', '_OPEN_ANGLE'):     ['[', '#ACTION_ITEM_SAVE', ']', '#ACTION_ITEM_ADD', 'MORE_TERM', 'ITEMIZE'],
    # TODO other types
    ('ITEM', '_TEXT'):           ['#ACTION_ITEM_ADD', 'MORE_TERM', 'ITEMIZE'],
    ('ITEM', '_DOLLAR'):         ['#ACTION_ITEM_ADD', 'MORE_TERM', 'ITEMIZE'],
    ('ITEM', '_OPEN_BRACKET'):   ['#ACTION_ITEM_ADD', 'MORE_TERM', 'ITEMIZE'],

    # --- TABULAR ---
    # <ALIGN> -> text <ALIGN>
    # <ALIGN> -> | <ALIGN>
    # <ALIGN> -> epsilon
    ('ALIGN', '_TEXT'):          ['#ACTION_ALIGN_SAVE', 'COL_WIDTH'],
    ('ALIGN', '_PIPE'):          ['|', '#ACTION_ALIGN_LINE', 'ALIGN'],
    ('ALIGN', '_CLOSE_CURLY'):   ['epsilon'],

    # <COL_WIDTH> -> { text } <ALIGN>
    # <COL_WIDTH> -> epsilon
    ('COL_WIDTH', '_OPEN_CURLY'): ['{', '#ACTION_COL_WIDTH', '}', 'ALIGN'],
    ('COL_WIDTH', 'epsilon'):     ['ALIGN'],

    # <TABLE> -> <CONST>
    # <TABLE> -> <COMMAND>
    # <TABLE> -> <BLOCK>
    # <TABLE> -> hline <TABLE>
    # <TABLE> -> cline { text } <TABLE>
    # <TABLE> -> enter <TABLE>
    # <TABLE> -> & <TABLE>
    # <TABLE> -> epsilon
    ('TABLE', '_TEXT'):          ['CONST', 'TABLE'],
    ('TABLE', 'hline'):          ['hline', '#ACTION_TABLE_HLINE', 'TABLE'],
    ('TABLE', 'cline'):          [ 'cline', '{', '#ACTION_TABLE_CLINE', '}', 'TABLE'],
    ('TABLE', '_ENTER'):         ['\\', '#ACTION_TABLE_NEW_ROW',  'TABLE'],
    ('TABLE', '_AMPERSAND'):     ['&',  '#ACTION_TABLE_NEW_CELL', 'TABLE'],
    ('TABLE', 'end'):            ['#ACTION_TABLE_CREATE'],
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
    ('TERM', '_OPEN_ANGLE'):      ['CONST'],
    ('TERM', '_CLOSE_ANGLE'):     ['CONST'],
    ('TERM', '_PIPE'):            ['CONST'],
    ('TERM', '_OPEN_BRACKET'):    ['CONST'],
    ('TERM', '_CLOSE_BRACKET'):   ['CONST'],

    # <TERM> -> <COMMAND>
    ('TERM', '_OPEN_CURLY'):      ['COMMAND'],
    ('TERM', 'sqrt'):             ['COMMAND'],
    ('TERM', 'frac'):             ['COMMAND'],
    ('TERM', 'dfrac'):            ['COMMAND'],
    ('TERM', 'sum'):              ['COMMAND'],
    ('TERM', 'prod'):             ['COMMAND'],
    ('TERM', 'int'):              ['COMMAND'],
    ('TERM', 'lim'):              ['COMMAND'],
    ('TERM', 'mathbb'):           ['COMMAND'],
    ('TERM', 'mathcal'):          ['COMMAND'],
    ('TERM', 'mathfrak'):         ['COMMAND'],
    ('TERM', '_SPACE_COMMAND'):   ['COMMAND'],
    ('TERM', '_MATH_SYMBOL'):     ['COMMAND'],

    # <TERM -> <BLOCK>
    ('TERM', 'begin'):            ['BLOCK'],

    # --- MORE_TERM ---
    # <MORE_TERM> -> <TERM> <MORE_TERM>
    ('MORE_TERM', '_TEXT'):          ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_SPECIAL_CHAR'):  ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'enter'):          ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_UNDERSCORE'):    ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_CARET'):         ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_OPEN_ANGLE'):    ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_CLOSE_ANGLE'):   ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_PIPE'):          ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_OPEN_BRACKET'):  ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_CLOSE_BRACKET'): ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_OPEN_CURLY'):    ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'sqrt'):           ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'frac'):           ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'dfrac'):          ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'sum'):            ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'prod'):           ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'int'):            ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'lim'):            ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'mathbb'):         ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'mathcal'):        ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'mathfrak'):       ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_SPACE_COMMAND'): ['TERM', 'MORE_TERM'],
    ('MORE_TERM', '_MATH_SYMBOL'):   ['TERM', 'MORE_TERM'],
    ('MORE_TERM', 'begin'):          ['TERM', 'MORE_TERM'],
    # <MORE_TERM> -> epsilon
    ('MORE_TERM', '_CLOSE_CURLY'):   ['epsilon'],
    ('MORE_TERM', 'end'):            ['epsilon'],
    ('MORE_TERM', '_DOLLAR'):        ['epsilon'],
    ('MORE_TERM', '\)'):             ['epsilon'],
    ('MORE_TERM', '\]'):             ['epsilon'],
    ('MORE_TERM', 'END'):            ['epsilon'],

    # --- CONST ---
    # <CONST> -> text
    ('CONST', '_TEXT'):              ['#ACTION_GENERATE_TEXT'],
    ('CONST', '_OPEN_ANGLE'):        ['#ACTION_GENERATE_TEXT'],
    ('CONST', '_CLOSE_ANGLE'):       ['#ACTION_GENERATE_TEXT'],
    ('CONST', '_PIPE'):              ['#ACTION_GENERATE_TEXT'],
    ('CONST', '_OPEN_BRACKET'):      ['#ACTION_GENERATE_TEXT'],
    ('CONST', '_CLOSE_BRACKET'):     ['#ACTION_GENERATE_TEXT'],

    # <CONST> -> special_char
    ('CONST', '_SPECIAL_CHAR'):      ['#ACTION_GENERATE_TEXT'],
    # <CONST> -> enter
    ('CONST', '_ENTER'):             ['enter'],
    # <CONST> -> index <EI_TERM> <EXP>
    ('CONST', '_UNDERSCORE'):        ['#ACTION_LEVEL_DOWN', '#ACTION_EI_INIT', 'EI_TERM', 'EXP'],
    # <CONST> -> exponent <EI_TERM> <IX>
    ('CONST', '_CARET'):             ['#ACTION_LEVEL_UP', '#ACTION_EI_INIT', 'EI_TERM', 'IX'],

    # --- EI_TERM ---
    # <EI_TERM> -> text
    ('EI_TERM', '_TEXT'):           ['#ACTION_GENERATE_TEXT'],
    # <EI_TERM> -> special_symbols
    ('EI_TERM', '_SPECIAL_CHAR'):   ['#ACTION_GENERATE_TEXT'],
    # <EI_TERM> -> { <MORE_TERM> }
    ('EI_TERM', '_OPEN_CURLY'):     ['COMMAND'],
    # <EI_TERM> -> <COMMAND>
    ('EI_TERM', 'sqrt'):            ['COMMAND'],
    ('EI_TERM', 'frac'):            ['COMMAND'],
    ('EI_TERM', 'dfrac'):           ['COMMAND'],
    ('EI_TERM', '_MATH_SYMBOL'):    ['COMMAND'],

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
    ('COMMAND', '_OPEN_CURLY'):     ['{', 'MORE_TERM', '}'],

    # <COMMAND> -> sqrt <SQRT>
    ('COMMAND', 'sqrt'):            ['sqrt', 'SQRT'],

    # <COMMAND> -> frac <FRAC>
    # <COMMAND> -> dfrac <FRAC>
    ('COMMAND', 'frac'):            ['frac',  '#ACTION_FRAC_SAVE_FRAC',  'FRAC'],
    ('COMMAND', 'dfrac'):           ['dfrac', '#ACTION_FRAC_SAVE_DFRAC', 'FRAC'],

    # <COMMAND> -> range_operators
    ('COMMAND', 'sum'):             ['#ACTION_RANGE_OP_INIT', 'RANGE_OP'],
    ('COMMAND', 'prod'):            ['#ACTION_RANGE_OP_INIT', 'RANGE_OP'],
    ('COMMAND', 'lim'):             ['#ACTION_RANGE_OP_INIT', 'RANGE_OP'],
    ('COMMAND', 'int'):             ['#ACTION_RANGE_OP_INIT'],

    ('RANGE_OP', '_UNDERSCORE'):    ['#ACTION_SAVE_RANGE_OP'],
    ('RANGE_OP', '_CARET'):         ['#ACTION_SAVE_RANGE_OP'],
    ('RANGE_OP', 'epsilon'):        ['epsilon'],

    # <COMMAND> -> command <MATH_FONT>
    ('COMMAND', 'mathbb'):          ['mathbb',   '{', '#ACTION_MATH_FONT_MATHBB',   'MATH_FONT', '}'],
    ('COMMAND', 'mathcal'):         ['mathcal',  '{', '#ACTION_MATH_FONT_MATHCAL',  'MATH_FONT', '}'],
    ('COMMAND', 'mathfrak'):        ['mathfrak', '{', '#ACTION_MATH_FONT_MATHFRAK', 'MATH_FONT', '}'],

    # <MATH_FONT> -> text <MATH_FONT>
    # <MATH_FONT> -> epsilon
    ('MATH_FONT', '_TEXT'):         ['#ACTION_GENERATE_MATH_LETTER', 'MATH_FONT'],
    ('MATH_FONT', '_CLOSE_CURLY'):  ['#ACTION_REMOVE_MATH_FONT'],

    # <COMMAND> -> space_commands
    ('COMMAND', '_SPACE_COMMAND'):  ['#ACTION_SPACE'],
    ('COMMAND', '_MATH_SYMBOL'):    ['#ACTION_MATH_SYMBOL'],

    # --- SQRT ---
    # <SQRT> -> [ <MORE_TERM> ] { <MORE_TERM> }
    ('SQRT', '_OPEN_ANGLE'): [
        '[', '#ACTION_SQRT_INDEX_BEGIN',     'MORE_TERM', ']',
        '{', '#ACTION_SQRT_INIT_WITH_INDEX', 'MORE_TERM', '}',
        '#ACTION_SQRT_CREATE'
    ],
    # <SQRT> -> { <MORE_TERM> }
    ('SQRT', '_OPEN_CURLY'): [
        '{', '#ACTION_SQRT_INIT', 'MORE_TERM', '}',
        '#ACTION_SQRT_CREATE'
    ],

    # --- FRAC ---
    # <FRAC> -> { <MORE_TERM> } { <MORE_TERM> }
    ('FRAC', '_OPEN_CURLY'): [
        '{', '#ACTION_FRAC_INIT', 'MORE_TERM', '}', '#ACTION_FRAC_UP',
        '{', 'MORE_TERM', '}', '#ACTION_FRAC_DOWN'
    ],

    # --- BLOCK ---
    # <BLOCK> -> begin { text } <MATRIX> end { text }
    ('BLOCK', 'begin'): [
        'begin', '{', '#ACTION_MATRIX_VERIFY_BEGIN', '}',
        '#ACTION_MATRIX_INIT',
        'MATRIX',
        '#ACTION_MATRIX_CREATE',
        'end',   '{', '#ACTION_MATRIX_VERIFY_END',   '}'
    ],

    # --- MATRIX ---
    # TODO add all possible values
    # <MATRIX> -> <CONST> <MATRIX>
    # <MATRIX> -> <COMMAND> <MATRIX>
    # <MATRIX> -> <BLOCK> <MATRIX>
    # <MATRIX> -> enter <MATRIX>
    # <MATRIX> -> & <MATRIX>
    # <MATRIX> -> epsilon
    ('MATRIX', '_TEXT'):            ['CONST', 'MATRIX'],
    ('MATRIX', '_SPECIAL_CHAR'):    ['CONST', 'MATRIX'],
    ('MATRIX', '_UNDERSCORE'):      ['CONST', 'MATRIX'],
    ('MATRIX', '_OPEN_CURLY'):      ['COMMAND', 'MATRIX'],
    ('MATRIX', '_MATH_SYMBOL'):     ['COMMAND', 'MATRIX'],
    ('MATRIX', 'sqrt'):             ['COMMAND', 'MATRIX'],
    ('MATRIX', 'frac'):             ['COMMAND', 'MATRIX'],
    ('MATRIX', 'begin'):            ['BLOCK', 'MATRIX'],
    ('MATRIX', '_ENTER'):           ['\\', '#ACTION_MATRIX_NEW_ROW',  'MATRIX'],
    ('MATRIX', '_AMPERSAND'):       ['&',  '#ACTION_MATRIX_NEW_CELL', 'MATRIX'],
    ('MATRIX', 'end'):              ['epsilon'],
}
