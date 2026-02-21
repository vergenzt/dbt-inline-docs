from dataclasses import replace
from typing import Any, Callable, Dict, Optional

from dbt.artifacts.resources.types import NodeType
from dbt.clients import jinja as dbt_jinja
from dbt.parser.base import ConfiguredParser
from dbt.contracts.graph.nodes import ParsedNode

from .parse import parse_inline_docs
from .utils import patch


@patch(dbt_jinja.get_rendered)
def render_template(
    orig: Callable[[str, Dict[str, Any], Any, bool, bool], str],
    string: str,
    ctx: Dict[str, Any],
    node=None,
    capture_macros: bool = False,
    native: bool = False,
):
    """Patch `render_template` to store the parse-time rendered Jinja on the node."""
    result = orig(string, ctx, node, capture_macros, native)
    if result and node and capture_macros:
        # capture_macros=True means this was a parsing run
        setattr(node, "parsed_code", result)
    return result


@patch(ConfiguredParser.parse_node)
def parse_node(orig, self, block):
    node = orig(self, block)
    if node.resource_type == NodeType.Model:
        parse_inline_docs(self, node)


@patch(ParsedNode.get_target_write_path)
def get_target_write_path(
    orig, self: ParsedNode, target_path: str, subdirectory: str, split_suffix: Optional[str] = None
) -> str:
    if self.resource_type == NodeType.Test and self.original_file_path.endswith(".sql"):
        self_suffixed = replace(
            self, original_file_path=self.original_file_path + ".inline-docs.yml"
        )
        return orig(self_suffixed, target_path, subdirectory, split_suffix)
    else:
        return orig(self, target_path, subdirectory, split_suffix)


ALL = patch.ALL
