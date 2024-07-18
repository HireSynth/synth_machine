import xmltodict
from copy import deepcopy
from partial_json_parser import loads, OBJ
import re

try:
    from enum import StrEnum
except ImportError:
    # For python versions <3.11, using aenum for backward compatibility
    from aenum import StrEnum


class ParserOptions(StrEnum):  # type: ignore
    STR = "str"
    CODE = "code"
    JSON = "json"
    XML = "xml"


class SynthParser:
    def __init__(self):
        self.parse = {
            "json": self.json_parse,
            "xml": self.xml_parse,
            "code": self.code_parse,
        }

    def json_parse(self, raw_value: str) -> dict | list:
        return loads(str(raw_value), OBJ)

    def xml_parse(self, raw_value: str) -> dict:
        open_tag_pattern = r"<[^/][^>]*>"
        close_tag_pattern = r"</[^>]+>"

        open_tags = re.findall(open_tag_pattern, raw_value)
        close_tags = re.findall(close_tag_pattern, raw_value)
        unclosed_tags = set(open_tags) - set(
            [val.replace("/", "") for val in deepcopy(close_tags)]
        )
        if unclosed_tags:
            raw_value += "".join(
                [
                    tag.replace("<", "</")
                    for tag in list(open_tags)[::-1]
                    if tag in unclosed_tags
                ]
            )
        return xmltodict.parse(raw_value)

    def code_parse(self, raw_value: str) -> str:
        code_break_points = raw_value.split("```")

        match len(code_break_points):
            case 0:
                return ""
            case 1:
                return raw_value
            case _:
                code_block = code_break_points[1]

        # Remove any language specifier
        first_line = code_block.split("\n", 1)[0]
        if first_line in _markdown_language_specifiers:
            code_block = code_block.strip(f"{first_line}\n")

        return code_block.rstrip().strip()


_markdown_language_specifiers = [
    "1c",
    "abnf",
    "accesslog",
    "actionscript",
    "ada",
    "arduino",
    "armasm",
    "asciidoc",
    "aspectj",
    "autohotkey",
    "autoit",
    "avrasm",
    "awk",
    "axapta",
    "bash",
    "basic",
    "bnf",
    "brainfuck",
    "cal",
    "capnproto",
    "ceylon",
    "clean",
    "clojure-repl",
    "clojure",
    "cmake",
    "coffeescript",
    "coq",
    "cos",
    "cpp",
    "crmsh",
    "crystal",
    "cs",
    "csharp",
    "csp",
    "css",
    "d",
    "dart",
    "delphi",
    "diff",
    "django",
    "dns",
    "dockerfile",
    "dos",
    "dsconfig",
    "dts",
    "dust",
    "ebnf",
    "elixir",
    "elm",
    "erb",
    "erlang-repl",
    "erlang",
    "excel",
    "fix",
    "flix",
    "fortran",
    "fsharp",
    "gams",
    "gauss",
    "gcode",
    "gherkin",
    "glsl",
    "go",
    "golo",
    "gradle",
    "groovy",
    "haml",
    "handlebars",
    "haskell",
    "haxe",
    "hsp",
    "htmlbars",
    "http",
    "hy",
    "inform7",
    "ini",
    "irpf90",
    "java",
    "javascript",
    "jboss-cli",
    "json",
    "julia-repl",
    "julia",
    "kotlin",
    "lasso",
    "ldif",
    "leaf",
    "less",
    "lisp",
    "livecodeserver",
    "livescript",
    "llvm",
    "lsl",
    "lua",
    "makefile",
    "markdown",
    "mathematica",
    "matlab",
    "maxima",
    "mel",
    "mercury",
    "mipsasm",
    "mizar",
    "mojolicious",
    "monkey",
    "moonscript",
    "n1ql",
    "nginx",
    "nimrod",
    "nix",
    "nsis",
    "objectivec",
    "ocaml",
    "openscad",
    "oxygene",
    "parser3",
    "perl",
    "pf",
    "php",
    "pony",
    "powershell",
    "processing",
    "profile",
    "prolog",
    "protobuf",
    "puppet",
    "purebasic",
    "python",
    "q",
    "qml",
    "r",
    "rib",
    "roboconf",
    "rsl",
    "ruby",
    "ruleslanguage",
    "rust",
    "scala",
    "scheme",
    "scilab",
    "scss",
    "shell",
    "smali",
    "smalltalk",
    "sml",
    "sqf",
    "sql",
    "stan",
    "stata",
    "step21",
    "stylus",
    "subunit",
    "swift",
    "taggerscript",
    "tap",
    "tcl",
    "tex",
    "thrift",
    "tp",
    "twig",
    "typescript",
    "vala",
    "vbnet",
    "vbscript-html",
    "vbscript",
    "verilog",
    "vhdl",
    "vim",
    "x86asm",
    "xl",
    "xml",
    "xquery",
    "yaml",
    "zephir",
    "terraform",
    "tofu",
    "js",
    "py",
    "sh",
    "c",
    "cpp",
    "ts",
    "md",
    "html",
    "css",
    "json",
    "yml",
    "bat",
    "cmd",
    "ps",
    "ps1",
    "tex",
    "latex",
    "plaintext",
    "text",
    "none",
    "console",
    "terminal",
    "bash",
    "zsh",
    "fish",
    "ksh",
    "asm",
    "nasm",
    "masm",
    "go",
    "golang",
    "rb",
    "pl",
    "fs",
    "f#",
    "cs",
    "jsx",
    "tsx",
    "vue",
    "sass",
    "styl",
    "ls",
    "coffee",
    "tf",
    "hcl",
    "docker",
    "Dockerfile",
    "docker-compose",
    "makefile",
    "Makefile",
    "toml",
    "properties",
    "conf",
    "config",
    "ini",
    "csv",
    "tsv",
    "xml",
    "xaml",
    "svg",
    "graphql",
    "gql",
    "solidity",
    "sol",
    "rego",
    "bicep",
    "nim",
    "v",
    "zig",
    "kt",
    "kts",
    "groovy",
    "gradle",
    "mojo",
    "🔥",
    "rs",
    "go-html-template",
]
