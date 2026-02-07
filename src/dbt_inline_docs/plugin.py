from typing import Callable, ClassVar, Self
from typing import Concatenate as Cat

from dbt.contracts.graph.manifest import Manifest
from dbt.contracts.graph.nodes import ManifestSQLNode
from dbt.plugins.manager import dbt_hook, dbtPlugin
from dbt.plugins.manifest import PluginNodes
from dbt.parser.manifest import ManifestLoader
from dbt.task.compile import CompileRunner


class patches[T, **P, R]:
    _patches: ClassVar[list["patches"]] = []

    def __init__(self, cls: type[T], method: Callable[Cat[T, P], R]) -> None:
        self.cls = cls
        self.method = method

    def __call__(self, replacement: Callable[Cat[Callable[Cat[T, P], R], T, P], R]):
        self._patches.append(self)  # for later installation
        self.replacement = replacement

        def wrapper(inst: T, *a: P.args, **kw: P.kwargs) -> R:
            return self.replacement(self.method, inst, *a, **kw)

        self.wrapper = wrapper
        return replacement

    def install(self):
        setattr(self.cls, self.method.__name__, self.wrapper)

    @classmethod
    def install_all(cls):
        for patch in cls._patches:
            patch.install()


class DbtInlineDocsPlugin(dbtPlugin):
    def initialize(self) -> None:
        patches.install_all()


# Note: I initially considered *subclassing* CompileRunner and monkey-patching
# CompileTask.get_runner_type to return the subclass. However the runners for subclasses of
# CompileTask (e.g. RunTask's ModelRunner) themselves subclass CompileRunner directly, meaning our
# changes would *only* affect the compile task, and not any others.


@patches((cls := ManifestLoader), cls.load_and_parse_macros)
def load_macros_with_doc_comment_checking(orig, self: ManifestLoader, project_parser_files):
    """Load macros - placeholder for future macro documentation support."""
    result = orig(self, project_parser_files)
    # Future: check macros for doc comments if needed
    return result


@patches((cls := ManifestLoader), cls.parse_project)
def parse_project_with_inline_docs(orig, self: ManifestLoader, project_parser_files, project):
    """
    Hook into parse_project to extract inline doc comments after parsing models.
    This is where we inject descriptions from @moddoc and @coldoc into the manifest.
    """
    from .parse import parse_doc_comments
    
    # First, let the normal parsing happen
    result = orig(self, project_parser_files, project)
    
    # Now process all nodes to extract inline documentation
    for unique_id, node in self.manifest.nodes.items():
        # Only process SQL nodes (models, seeds, etc.)
        if not hasattr(node, 'raw_code'):
            continue
            
        raw_sql = node.raw_code
        if not raw_sql:
            continue
        
        # Parse doc comments from the SQL
        doc_comments = parse_doc_comments(raw_sql)
        
        if not doc_comments:
            continue
        
        # Process moddoc comments (model-level documentation)
        for comment in doc_comments:
            if comment.tag == 'moddoc':
                # Set model description
                if not node.description:  # Don't override existing descriptions
                    node.description = comment.description
            
            elif comment.tag == 'coldoc' and comment.column_name:
                # Set column description
                # Ensure columns dict exists
                if not hasattr(node, 'columns') or node.columns is None:
                    node.columns = {}
                
                # Find or create column entry
                column_name = comment.column_name
                if column_name not in node.columns:
                    # Create a new column entry
                    from dbt.contracts.graph.nodes import ColumnInfo
                    node.columns[column_name] = ColumnInfo(
                        name=column_name,
                        description=comment.description
                    )
                elif not node.columns[column_name].description:
                    # Update existing column if it has no description
                    node.columns[column_name].description = comment.description
    
    return result

