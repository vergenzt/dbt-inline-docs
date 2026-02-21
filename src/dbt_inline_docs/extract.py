import re
from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property
from io import StringIO
from textwrap import dedent
from typing import Any, ClassVar, Dict, Iterator, Optional

import yaml
from dbt.clients.yaml_helper import load_yaml_text
from dbt.parser.base import FinalNode


@dataclass
class DocCommentTypeValue:
    tag: str

    @property
    def full_tag(self):
        return f"@{self.tag}doc"

    _tags: ClassVar["dict[str, DocCommentTypeValue]"] = {}

    def __post_init__(self):
        self._tags[self.tag] = self

    def __str__(self):
        return f"Doc comment type `{self.full_tag}`"


class DocCommentType(DocCommentTypeValue, Enum):
    MODEL = "mod"
    COLUMN = "col"
    # TODO: "arg" type for macro args. (but how will it be inlined with the arg definition? jinja extension?)

    @classmethod
    def from_tag(cls, tag: str) -> "DocCommentType":
        try:
            return cls._tags[tag]
        except KeyError:
            raise ValueError(f"Unrecognized doc comment tag: `@{tag}doc`")


DOC_COMMENT_PATTERN = re.compile(
    r"""
        (?P<column> \w+ )? \s*
        /\*\* \s*
        (?P<body> 
            @ (?P<tag> \w+ ) doc \s+
            .*? \s*
        )
        [\*]* \*/
    """,
    re.VERBOSE | re.DOTALL | re.MULTILINE,
)


@dataclass
class DocComment:
    match: re.Match
    node: FinalNode

    type: DocCommentType = field(init=False)
    column: Optional[str] = field(init=False)
    body: str = field(init=False)
    description: str = field(init=False)
    properties: Dict[str, Any] = field(init=False)

    @classmethod
    def find_all(cls, code: str, node: FinalNode) -> Iterator["DocComment"]:
        for match in DOC_COMMENT_PATTERN.finditer(code):
            yield cls(match, node)

    @cached_property
    def loc(self):
        lineno = self.match.string[: self.match.pos].count("\n") + 1
        return f"{self.node.original_file_path}:{lineno}"

    def __post_init__(self):
        self._parse_body()

    def _parse_body(self):
        self.type = DocCommentType.from_tag(self.match["tag"])

        if self.type == DocCommentType.COLUMN:
            if column := self.match.group("column"):
                self.column = column
            else:
                raise ValueError(
                    f"{self.type} expects to be preceeded by a column identifier "
                    f"and optional whitespace, but no identifier was matched: {self.loc}"
                )
        else:
            self.column = None

        # dedent everything *except* the first line
        raw_body: str = self.match.group("body")
        assert raw_body.startswith(self.type.full_tag)
        raw_body_notag = raw_body[len(self.type.full_tag):].strip()
        head, *tail = raw_body_notag.splitlines(keepends=True)
        self.body = head + dedent("".join(tail))

        yaml_sep: Optional[re.Match] = None
        yaml_seps = list(re.finditer("^(---(?:-*))\n?", self.body, re.M))
        if len(yaml_seps) > 1:
            max_sep_len = max(sep.end(1) - sep.start(1) for sep in yaml_seps)
            longest_seps = [sep for sep in yaml_seps if sep.endpos - sep.pos == max_sep_len]
            if len(longest_seps) > 1:
                raise ValueError(
                    f"Found more than one yaml separator line in doc comment: {self.loc}"
                )
            else:
                yaml_sep = longest_seps[0]
        elif len(yaml_seps) == 1:
            yaml_sep = yaml_seps[0]

        if yaml_sep:
            start, end = yaml_sep.span()
            self.description = self.body[:start].strip()
            yaml_str = self.body[end:]
            self.properties = load_yaml_text(yaml_str)
        else:
            self.description = self.body
            self.properties = {}

    def all_properties(self):
        return {
            "name": self.column or self.node.name,
            "description": self.description,
            **(self.properties or {}),
        }
