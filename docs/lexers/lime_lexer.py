"""
Pygments lexer for the Lime / MGX scripting language.

Lime scripts (.mgx) embed the Margarita templating language and add
lime-specific decorator nodes:

    @state var = value
    @memory var / @memory delete var / @memory clear
    @effect run / log / input / func / tools / context

Other syntax features:
    from module import func        -- Python-style imports
    if / elif / else / for / in    -- control flow
    << ... >>                      -- output / prompt blocks
    ${var}                         -- variable interpolation
    // ...                         -- single-line comments
    => var                         -- assignment arrow
"""

from pygments.lexer import RegexLexer, bygroups
from pygments.token import (
    Comment,
    Generic,
    Keyword,
    Name,
    Number,
    Operator,
    Punctuation,
    String,
    Text,
    Whitespace,
)

__all__ = ["LimeLexer"]

# Subcommands that follow @effect
_EFFECT_CMDS = r"(run|log|input|func|tools|context)"
# Subcommands that follow @memory
_MEMORY_CMDS = r"(delete|clear|var)"


class LimeLexer(RegexLexer):
    """
    Lexer for Lime / MGX scripting language.

    Handles both Margarita template syntax and Lime-specific decorator nodes.
    """

    name = "Lime"
    aliases = ["lime", "mgx", "margarita", "marg", "mg", "margaritascript"]
    filenames = ["*.mgx", "*.mg", "*.margarita"]
    mimetypes = ["text/x-lime", "text/x-margarita"]

    tokens = {
        "root": [
            # Single-line comments  (// ...)
            (r"//.*?$", Comment.Single),
            # ----- Lime decorator nodes -----
            # @state var = value
            (
                r"(@state)(\s+)([a-zA-Z_]\w*)(\s*)(=)(\s*)",
                bygroups(
                    Keyword.Declaration,
                    Whitespace,
                    Name.Variable,
                    Whitespace,
                    Operator,
                    Whitespace,
                ),
                "state-value",
            ),
            # @memory delete/clear/var <name>
            (
                r"(@memory)(\s+)" + _MEMORY_CMDS + r"(\s+)([a-zA-Z_]\w*)",
                bygroups(
                    Keyword.Declaration,
                    Whitespace,
                    Keyword,
                    Whitespace,
                    Name.Variable,
                ),
            ),
            # @memory clear  (no name)
            (
                r"(@memory)(\s+)(clear)\b",
                bygroups(Keyword.Declaration, Whitespace, Keyword),
            ),
            # @memory var_name  (bare — create memory variable)
            (
                r"(@memory)(\s+)([a-zA-Z_]\w*)",
                bygroups(Keyword.Declaration, Whitespace, Name.Variable),
            ),
            # @effect context clear
            (
                r"(@effect)(\s+)(context)(\s+)(clear)\b",
                bygroups(
                    Keyword.Declaration,
                    Whitespace,
                    Keyword,
                    Whitespace,
                    Keyword,
                ),
            ),
            # @effect run
            (
                r"(@effect)(\s+)(run)\b",
                bygroups(Keyword.Declaration, Whitespace, Keyword),
            ),
            # @effect log "message with optional ${var}"
            (
                r'(@effect)(\s+)(log)(\s+)(")',
                bygroups(
                    Keyword.Declaration,
                    Whitespace,
                    Keyword,
                    Whitespace,
                    String.Double,
                ),
                "effect-string",
            ),
            # @effect input "question" => var
            (
                r'(@effect)(\s+)(input)(\s+)(")',
                bygroups(
                    Keyword.Declaration,
                    Whitespace,
                    Keyword,
                    Whitespace,
                    String.Double,
                ),
                "effect-string-arrow",
            ),
            # @effect func call(args) => result
            (
                r"(@effect)(\s+)(func)(\s+)",
                bygroups(
                    Keyword.Declaration,
                    Whitespace,
                    Keyword,
                    Whitespace,
                ),
                "effect-func",
            ),
            # @effect tools func(args) => result
            (
                r"(@effect)(\s+)(tools)(\s+)",
                bygroups(
                    Keyword.Declaration,
                    Whitespace,
                    Keyword,
                    Whitespace,
                ),
                "effect-func",
            ),
            # Generic @effect fallback
            (
                r"(@effect)(\s+)" + _EFFECT_CMDS,
                bygroups(Keyword.Declaration, Whitespace, Keyword),
            ),
            # ----- Python-style imports -----
            (
                r"(from)(\s+)([a-zA-Z_][\w.]*)(\s+)(import)(\s+)([a-zA-Z_]\w*)",
                bygroups(
                    Keyword,
                    Whitespace,
                    Name.Namespace,
                    Whitespace,
                    Keyword,
                    Whitespace,
                    Name.Function,
                ),
            ),
            # ----- Control flow -----
            # else: (no expression)
            (r"^(\s*)(else)(\s*)(:)", bygroups(Whitespace, Keyword, Whitespace, Punctuation)),
            # if / elif / for  <expression>:
            (
                r"^(\s*)(if|elif|for)(\s+)",
                bygroups(Whitespace, Keyword, Whitespace),
                "control-expr",
            ),
            # ----- Output / prompt blocks  << ... >> -----
            (r"<<<", String.Delimiter, "output-block"),
            (r"<<", String.Delimiter, "output-block"),
            # ----- Variable interpolation  ${...} -----
            (r"\$\{", Name.Variable, "variable"),
            # Plain text / whitespace
            (r"[^\n]", Text),
            (r"\n", Whitespace),
        ],
        # ---- State value: everything after  @state var =  until EOL ----
        "state-value": [
            # Inline comment
            (r"//.*?$", Comment.Single, "#pop"),
            # String values
            (r'"[^"]*"', String.Double, "#pop"),
            (r"'[^']*'", String.Single, "#pop"),
            # Lists / dicts (simple single-line)
            (r"(\[)([^\]]*?)(\])", bygroups(Punctuation, Generic.Output, Punctuation), "#pop"),
            (r"(\{)([^\}]*?)(\})", bygroups(Punctuation, Generic.Output, Punctuation), "#pop"),
            # Numbers
            (r"-?\d+\.?\d*", Number, "#pop"),
            # Booleans / null
            (r"\b(True|False|None)\b", Keyword.Constant, "#pop"),
            # Identifier reference
            (r"[a-zA-Z_]\w*", Name.Variable, "#pop"),
            # Fallback rest of line
            (r"[^\n]+", Text, "#pop"),
            (r"\n", Whitespace, "#pop"),
        ],
        # ---- String for @effect log "..." ----
        "effect-string": [
            (r"\$\{[a-zA-Z_][\w.]*\}", Name.Variable),
            (r'"', String.Double, "#pop"),
            (r'[^"$]+', String.Double),
            (r"\$", String.Double),
        ],
        # ---- String + => var for @effect input "..." => var ----
        "effect-string-arrow": [
            (r"\$\{[a-zA-Z_][\w.]*\}", Name.Variable),
            (r'"(\s*)(=>)(\s*)([a-zA-Z_]\w*)', bygroups(String.Double, Operator, Whitespace, Name.Variable), "#pop"),
            (r'"', String.Double, "#pop"),
            (r'[^"$]+', String.Double),
            (r"\$", String.Double),
        ],
        # ---- @effect func/tools  call(args) => result ----
        "effect-func": [
            # function name
            (r"[a-zA-Z_]\w*", Name.Function, "effect-func-args"),
            (r"[ \t]+", Whitespace),
            # newline ends the statement and pops back to root
            (r"\n", Whitespace, "#pop"),
        ],
        "effect-func-args": [
            (r"\(", Punctuation),
            (r"\)", Punctuation),
            # => result
            (r"([ \t]*)(=>)([ \t]*)([a-zA-Z_]\w*)", bygroups(Whitespace, Operator, Whitespace, Name.Variable), "#pop"),
            # typed parameters:  name: type
            (r"([a-zA-Z_]\w*)(\s*:\s*)([a-zA-Z_]\w*)", bygroups(Name.Variable, Punctuation, Name.Builtin)),
            (r"[a-zA-Z_]\w*", Name.Variable),
            (r",", Punctuation),
            (r"[ \t]+", Whitespace),
            (r"[^\n]", Text),
            (r"\n", Whitespace, "#pop"),
        ],
        # ---- Control expression (if/elif/for)  ...  : ----
        "control-expr": [
            (r"\b(in|and|or|not|True|False|None)\b", Keyword.Operator),
            (r"\b(range)(\s*)(\()", bygroups(Name.Builtin, Whitespace, Punctuation), "func-args"),
            (r"==|!=|<=|>=|<|>", Operator),
            (r"[a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*", Name.Variable),
            (r'"[^"]*"', String.Double),
            (r"'[^']*'", String.Single),
            (r"\d+", Number.Integer),
            (r",", Punctuation),
            (r":", Punctuation, "#pop"),
            (r"\s+", Whitespace),
        ],
        "func-args": [
            (r"\d+", Number.Integer),
            (r",", Punctuation),
            (r"\)", Punctuation, "#pop"),
            (r"\s+", Whitespace),
        ],
        # ---- Output block  << ... >> ----
        "output-block": [
            # Variables inside output blocks
            (r"\$\{[a-zA-Z_][\w.]*\}", Name.Variable),
            (r"\$\{", Name.Variable, "variable"),
            # Closing
            (r">>>", String.Delimiter, "#pop"),
            (r">>", String.Delimiter, "#pop"),
            # Content lines
            (r"[^>$\n]+", Generic.Output),
            (r"\n", Whitespace),
            (r".", Generic.Output),
        ],
        # ---- Variable  ${...} ----
        "variable": [
            (r"[a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*", Name.Variable),
            (r"\}", Name.Variable, "#pop"),
            (r"\s+", Whitespace),
        ],
    }
