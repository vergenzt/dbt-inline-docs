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
    result = orig(self, project_parser_files)

    for name, macro in self.manifest.macros.items():

    return result


def 


@patches((cls := CompileRunner), cls.compile)
def compile_and_add_docs(orig, self, manifest: Manifest) -> ManifestSQLNode:
    """
    Replacement for CompileRunner.compile which incorporates inline @modeldoc and @coldoc
    comments into model and column properties.

    Problem: How do we
    """
    compiled = orig(self, manifest)

    # ...

    return compiled
