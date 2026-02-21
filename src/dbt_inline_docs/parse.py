from dataclasses import replace

from dbt.contracts.files import ParseFileType, SchemaSourceFile
from dbt.parser.base import FinalNode, Parser
from dbt.parser.schemas import SchemaParser
from dbt.parser.search import FileBlock
from dbt_common.utils import deep_merge

from .extract import DocComment


def parse_inline_docs(node_parser: Parser[FinalNode], node: FinalNode):
    """
    Parse any inline node docs, updating the node in-place with their contents.
    """
    code = getattr(node, "parsed_code", None) or getattr(node, "raw_code", None)
    if not code:
        return

    docs = list(DocComment.find_all(code, node))
    if not docs:
        return

    node_dct = {"name": node.name}
    for doc in docs:
        if doc.column:
            column = doc.all_properties()
            columns = node_dct.setdefault("columns", [])
            columns.append(column)

        else:
            prev_description = node_dct.get("description")
            node_dct = deep_merge(node_dct, doc.all_properties())

            if prev_description:
                node_dct["description"] = f"{prev_description}\n\n{doc.description}"

    schema_parser = SchemaParser(
        node_parser.project, node_parser.manifest, node_parser.root_project
    )
    node_source_file = node_parser.manifest.files[node.file_id]
    node_schema_dct = {node.resource_type.pluralize(): [node_dct]}

    fake_schema_source_file = SchemaSourceFile(
        node_source_file.path,
        node_source_file.checksum,
        node.package_name,
        ParseFileType.Schema,
        dfy=node_schema_dct,
    )
    fake_schema_source_block = FileBlock(fake_schema_source_file)

    # ensure the schema parser can find the main node
    node_parser.manifest.ref_lookup.add_node(node)

    schema_parser.parse_file(fake_schema_source_block, node_schema_dct)
