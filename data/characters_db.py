# ---------------------------------------------------------------------------
# File name   : characters_db.py
# Created By  : Katarina Strenkova
# ---------------------------------------------------------------------------

MIN_SPACE =  0.1
SMALL_SPACE = 0.2
BASE_SPACE = 0.3
GRID_SPACE = 0.5
LINE_SPACE = 1.0
INDENTATION = 0.6
PAR_SPACE = 2.0  # TODO change 2.0 for the correct value

LINE_THICKNESS = 0.025
SQRT_WIDTH = 0.855927586555481

# numeric values of space commands
space_sizes = {
    '!':    -0.1,
    ',':     0.15,
    ':':     0.2,
    ';':     0.25,
    ' ':     0.3,
    'quad':  0.6,
    'qquad': 1.2
}

# all supported matrix bracket types
matrix_brackets = {
    'matrix':  ('', ''),
    'bmatrix': ('[', ']'),
    'Bmatrix': ('{', '}'),
    'pmatrix': ('(', ')'),
    'vmatrix': ('|', '|'),
    'Vmatrix': ('||', '||')
}

# structural tokens that have syntactic meaning
char_type = {
    '\\': 'BACKSLASH',
    '{': '_OPEN_CURLY',
    '(': '_OPEN_BRACKET',
    '[': '_OPEN_ANGLE',
    '}': '_CLOSE_CURLY',
    ')': '_CLOSE_BRACKET',
    ']': '_CLOSE_ANGLE',
    '|': '_PIPE',
    '^': '_CARET',
    '_': '_UNDERSCORE',
    '&': '_AMPERSAND',
    '$': '_DOLLAR',
}

# characters that can be escaped with a backslash
# to render literally (e.g., \{, \$, ...)
special_chars = [
    '_OPEN_CURLY',
    '_CLOSE_CURLY',
    '_CARET',
    '_UNDERSCORE',
    '_AMPERSAND',
    '_DOLLAR',
]

# block types and their setup actions
block_actions = {
    # math mode
    'math':        '#ACTION_MATH_MODE_INLINE',
    'equation':    '#ACTION_MATH_MODE_DISPLAY',
    'displaymath': '#ACTION_MATH_MODE_DISPLAY',

    # bullet points
    'enumerate':    '#ACTION_ITEM_INIT',
    'itemize':      '#ACTION_ITEM_INIT',

    # tables
    'tabular':      '#ACTION_TABLE_INIT'
}

# context-dependent epsilon productions
epsilon_rules = {
    # stack_top: token.type, token.value
    'ITEMIZE':   [('COMMAND', 'item')],
    'COL_WIDTH': [('_OPEN_CURLY', '{')],
    'IX':        [('_UNDERSCORE', '_')],
    'EXP':       [('_CARET', '^')],
    'RANGE_OP':  [
        ('_UNDERSCORE', '_'),
        ('_CARET', '^')
    ]
}

# tokens that end math mode
end_tokens = {
    ('_DOLLAR', '$'),
    ('COMMAND', '\)'),
    ('COMMAND', '\]'),
    ('COMMAND', 'end')
}

# supported width units
units = ['cm', 'pt', 'in', 'em', 'mm']

# supported table alignment types
table_alignments =  ['c', 'l', 'r', 'p', 'm', 'b']

# UNICODE DATABASE

# TODO math accents
# 'hat': '\u0302',
# 'tilde': '\u0303',
# 'bar': '\u0304',
# 'vec': '\u20d7',
# 'dot': '\u0307',
# 'ddot': '\u0308',

# TODO wide version maybe
# \widehat{...}
# \widetilde{...}
# \overline{...}
# \underline{...}
# \overbrace{...}
# \underbrace{...}

unicode_chars = {
    # lower case greek alphabet
    'alpha': '\u03b1',
    'beta': '\u03b2',
    'gamma': '\u03b3',
    'delta': '\u03b4',
    'epsilon': '\u03f5',
    'varepsilon': '\u03b5',
    'zeta': '\u03b6',
    'eta': '\u03b7',
    'theta': '\u03b8',
    'vartheta': '\u03d1',
    'iota': '\u03b9',
    'kappa': '\u03ba',
    'lambda': '\u03bb',
    'mu': '\u03bc',
    'nu': '\u03bd',
    'xi': '\u03be',
    'omicron': '\u03bf',
    'pi': '\u03c0',
    'varpi': '\u03d6',
    'rho': '\u03c1',
    'varrho': '\u03f1',
    'sigma': '\u03c3',
    'varsigma': '\u03c2',
    'tau': '\u03c4',
    'upsilon': '\u03c5',
    'phi': '\u03d5',
    'varphi': '\u03c6',
    'chi': '\u03c7',
    'psi': '\u03c8',
    'omega': '\u03c9',

    # upper case greek alphabet
    'Gamma': '\u0393',
    'Delta': '\u0394',
    'Theta': '\u0398',
    'Lambda': '\u039b',
    'Xi': '\u039e',
    'Pi': '\u03a0',
    'Sigma': '\u03a3',
    'Upsilon': '\u03a5',
    'Phi': '\u03a6',
    'Psi': '\u03a8',
    'Omega': '\u03a9',

    # relation operators
    'in': '\u2208',
    'notin': '\u2209',
    'ni': '\u220b',
    'propto': '\u221d',
    'mid': '\u2223',
    'parallel': '\u2225',
    'nparallel': '\u2226',
    'sim': '\u223c',
    'simeq': '\u2243',
    'cong': '\u2245',
    'approx': '\u2248',
    'asymp': '\u224d',
    'doteq': '\u2250',
    'ne': '\u2260',
    'neq': '\u2260',
    'equiv': '\u2261',
    'le': '\u2264',
    'ge': '\u2265',
    'leq': '\u2264',
    'geq': '\u2265',
    'leqslant': '\u2264',
    'geqslant': '\u2265',
    'll': '\u226a',
    'gg': '\u226b',
    'nless': '\u226e',
    'ngtr': '\u226f',
    'nleq': '\u2270',
    'ngeq': '\u2271',
    'nleqslant': '\u2270',
    'ngeqslant': '\u2271',
    'prec': '\u227a',
    'succ': '\u227b',
    'preceq': '\u227c',
    'succeq': '\u227d',
    'nprec': '\u2280',
    'nsucc': '\u2281',
    'subset': '\u2282',
    'supset': '\u2283',
    'subseteq': '\u2286',
    'supseteq': '\u2287',
    'nsubseteq': '\u2288',
    'nsupseteq': '\u2289',
    'sqsubset': '\u228f',
    'sqsupset': '\u2290',
    'sqsubseteq': '\u2291',
    'sqsupseteq': '\u2292',
    'vdash': '\u22a2',
    'dashv': '\u22a3',
    'perp': '\u22a5',
    'models': '\u22a7',
    'bowtie': '\u22c8',
    'lll': '\u22d8',
    'ggg': '\u22d9',
    'npreceq': '\u22e0',
    'nsucceq': '\u22e1',
    'frown': '\u2322',
    'smile': '\u263a',

    # binary operators
    'ast': '*',
    'pm': '\xb1',
    'times': '\xd7',
    'div': '\xf7',
    'dagger': '\u2020',
    'ddagger': '\u2021',
    'bullet': '\u2022',
    'ldots': '\u2026',
    'amalg': '\u2210',
    'mp': '\u2213',
    'setminus': '\u2216',
    'circ': '\u2218',
    'wedge': '\u2227',
    'vee': '\u2228',
    'cap': '\u2229',
    'cup': '\u222a',
    'wr': '\u2240',
    'uplus': '\u228e',
    'sqcap': '\u2293',
    'sqcup': '\u2294',
    'oplus': '\u2295',
    'ominus': '\u2296',
    'otimes': '\u2297',
    'oslash': '\u2298',
    'odot': '\u2299',
    'boxtimes': '\u22a0',
    'diamond': '\u22c4',
    'cdot': '\u22c5',
    'star': '\u22c6',
    'Box': '\u25a1',
    'bigtriangleup': '\u25b3',
    'triangleright': '\u25b9',
    'bigtriangledown': '\u25bd',
    'triangleleft': '\u25c3',

    # logic notation
    'neg': '\xac',
    'implies': '\u21d2',
    'Leftarrow': '\u21d0',
    'Rightarrow': '\u21d2',
    'Leftrightarrow': '\u21d4',
    'iff': '\u21d4',
    'forall': '\u2200',
    'exists': '\u2203',
    'nexists': '\u2204',
    'land': '\u2227',
    'lor': '\u2228',
    'top': '\u22a4',
    'bot': '\u22a5',

    # arrows
    'leftarrow': '\u2190',
    'gets': '\u2190',
    'uparrow': '\u2191',
    'rightarrow': '\u2192',
    'to': '\u2192',
    'downarrow': '\u2193',
    'leftrightarrow': '\u2194',
    'updownarrow': '\u2195',
    'nleftarrow': '\u219a',
    'nrightarrow': '\u219b',
    'mapsto': '\u21a6',
    'Uparrow': '\u21d1',
    'Downarrow': '\u21d3',
    'Updownarrow': '\u21d5',
    'rightleftharpoons': '\u21cc',
    'nLeftrightarrow': '\u21ce',
    'leadsto': '\u21dc',
    'nwarrow': '\u2196',
    'nearrow': '\u2197',
    'searrow': '\u2198',
    'swarrow': '\u2199',
    'leftharpoonup': '\u21bc',
    'leftharpoondown': '\u21bd',
    'rightharpoonup': '\u21c0',
    'rightharpoondown': '\u21c1',
    'longmapsto': '\u27fc',

    # brackets
    'lceil': '\u2308',
    'rceil': '\u2309',
    'lfloor': '\u230a',
    'rfloor': '\u230b',
    'ulcorner': '\u231c',
    'urcorner': '\u231d',
    'llcorner': '\u231e',
    'lrcorner': '\u231f',
    'langle': '\u27e8',
    'rangle': '\u27e9',

    # other symbols
    'backslash': '\\',
    'neg': '\u00ac',
    'hbar': '\u0127',
    'prime': '\u2032',
    'Im': '\u2111',
    'ell': '\u2113',
    'wp': '\u2118',
    'Re': '\u211c',
    'complement': '\u2201',
    'partial': '\u2202',
    'emptyset': '\u2205',
    'nabla': '\u2207',
    'surd': '\u221a',
    'infty': '\u221e',
    'angle': '\u2220',
    'therefore': '\u2234',
    'because': '\u2235',
    'vdots': '\u22ee',
    'cdots': '\u22ef',
    'ddots': '\u22f1',
    'varnothing': '\u2300',
    'blacksquare': '\u25a0',
    'square': '\u25a1',
    'triangle': '\u25b3',
}

unicode_chars_big = {
    # big symbols
    'prod': '\u220f',
    'sum': '\u2211',
    'int': '\u222b',
    'oint': '\u222e',
    'bigcup': '\u22c3',
    'bigcap': '\u22c2',
    'bigvee': '\u22c1',
    'bigwedge': '\u22c0'
}

unicode_fonts = {
    'mathbb': {
        'A': '\U0001D538', 'B': '\U0001D539', 'C': '\u2102',     'D': '\U0001D53B',
        'E': '\U0001D53C', 'F': '\U0001D53D', 'G': '\U0001D53E', 'H': '\u210D',
        'I': '\U0001D540', 'J': '\U0001D541', 'K': '\U0001D542', 'L': '\U0001D543',
        'M': '\U0001D544', 'N': '\u2115',     'O': '\U0001D546', 'P': '\u2119',
        'Q': '\u211A',     'R': '\u211D',     'S': '\U0001D54A', 'T': '\U0001D54B',
        'U': '\U0001D54C', 'V': '\U0001D54D', 'W': '\U0001D54E',
        'X': '\U0001D54F', 'Y': '\U0001D550', 'Z': '\u2124',
    },
    'mathcal': {
        'A': '\U0001D49C', 'B': '\u212C',     'C': '\U0001D49E', 'D': '\U0001D49F',
        'E': '\u2130',     'F': '\u2131',     'G': '\U0001D4A2', 'H': '\u210B',
        'I': '\u2110',     'J': '\U0001D4A5', 'K': '\U0001D4A6', 'L': '\u2112',
        'M': '\u2133',     'N': '\U0001D4A9', 'O': '\U0001D4AA', 'P': '\U0001D4AB',
        'Q': '\U0001D4AC', 'R': '\u211B',     'S': '\U0001D4AE', 'T': '\U0001D4AF',
        'U': '\U0001D4B0', 'V': '\U0001D4B1', 'W': '\U0001D4B2',
        'X': '\U0001D4B3', 'Y': '\U0001D4B4', 'Z': '\U0001D4B5'
    },
    'mathfrak': {
        'A': '\U0001D504', 'B': '\U0001D505', 'C': '\u212D',     'D': '\U0001D507',
        'E': '\U0001D508', 'F': '\U0001D509', 'G': '\U0001D50A', 'H': '\u210C',
        'I': '\u2111',     'J': '\U0001D50D', 'K': '\U0001D50E', 'L': '\U0001D50F',
        'M': '\U0001D510', 'N': '\U0001D511', 'O': '\U0001D512', 'P': '\U0001D513',
        'Q': '\U0001D514', 'R': '\u211C',     'S': '\U0001D516', 'T': '\U0001D517',
        'U': '\U0001D518', 'V': '\U0001D519', 'W': '\U0001D51A',
        'X': '\U0001D51B', 'Y': '\U0001D51C', 'Z': '\u2128',
    }
}
