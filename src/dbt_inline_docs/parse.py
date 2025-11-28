"""
Functions which will have to hook into dbt project *parsing* in order to extract [model
properties](https://docs.getdbt.com/reference/model-properties) which are specified in @*doc
comments.
"""

from enum import Enum, auto
import re
from typing import Iterable, Literal
from jinja2 import Environment
from jinja2.ext import Extension
from jinja2.lexer import TokenStream, Token

DOC_COMMENT_OPEN_RE = re.compile(rf"{re.escape("/**")} \s* @ (?P<tag> modeldoc | coldoc ) \b", re.VERBOSE)





class JinjaDocCommentExtension(Extension):
    """
    This extension implements support for inline @modeldoc and @coldoc comments, translating them
    into ???
    """

    tags = {"modeldoc", "coldoc"}

    def filter_stream(self, stream: TokenStream) -> Iterable[Token]:
        state: Literal["out", "in"] = "out"

        for token in stream:
            match state, token:
                case "out", Token(lineno, "data", val) if (match := DOC_COMMENT_OPEN_RE.match(val)):
                    yield 
                    ...
                case _:
                    yield token

    def _handle_modeldoc_call(self, )





def search_raw_sql_for_doc_comments(sql: str):
    """
    Search for @*doc comments in the raw (uncompiled) SQL of the given node.

    Let's search macros too - so we can mark any which themselves yield @*doc comments.

    @*doc comments which contain anything that needs to be known by the end of parsing (TBD what all
    exactly that is, but at minimum it includes test nodes). (Will need to come up with an allowlist
    of what all can be present.)
    """
