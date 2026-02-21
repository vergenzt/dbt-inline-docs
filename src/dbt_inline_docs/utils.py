from copy import copy
from inspect import signature
from typing import TYPE_CHECKING, Callable, ClassVar, List


class patch:
    ALL: ClassVar = []

    def __init__(self, callable: Callable) -> None:
        self.callable = callable

    def __call__(self, wrapper):
        self.ALL.append(self)  # for later installation
        self.wrapper = wrapper
        self.wrapper.__replaces_ref__ = self.callable
        self.wrapper.__patch__ = self
        return wrapper

    def install(self):
        wrap = self.wrapper
        wrap_name = wrap.__name__
        wrap_mod = wrap.__module__

        orig = wrap.__replaces_ref__
        orig_name = orig.__name__
        orig_globals = orig.__globals__

        notypes = copy(orig)
        notypes.__annotations__ = {}
        sig_notypes = signature(notypes)

        orig_code_holder_globals = {**orig_globals}
        orig_code_holder_code = f"def {orig_name}{sig_notypes}:\n\tpass\n"
        exec(orig_code_holder_code, orig_code_holder_globals)
        orig_code_holder = self.wrapper.__replaces_orig__ = orig_code_holder_globals[orig_name]
        orig_code_holder.__code__ = orig.__code__

        repl_code = (
            f"def {orig_name}{sig_notypes}:\n"
            f"  from inspect import signature, BoundArguments\n"
            f"  from {wrap_mod} import {wrap_name}\n"
            f"  sig = signature({wrap_name}.__replaces_orig__)\n"
            f"  bound = BoundArguments(sig, locals())\n"
            f"  return {wrap_name}({wrap_name}.__replaces_orig__, *bound.args, **bound.kwargs)\n"
        )
        repl_globals = {**orig_globals}
        exec(repl_code, repl_globals)
        repl = repl_globals[orig_name]
        self.replacement = repl

        orig.__code__ = repl.__code__
        # setattr(self.obj, self.callable.__name__, self.wrapper)


if TYPE_CHECKING:
    from typing import Concatenate as Cat
    from typing import ParamSpec, TypeVar

    P = ParamSpec("MethodParams")
    R = TypeVar("MethodReturn")

    class patch:
        ALL: ClassVar[List["patch"]]
        FnObj = Callable[P, R]
        FnWrapper = Callable[Cat[FnObj, P], R]

        def __init__(self, method: FnObj) -> None: ...

        def __call__(self, replacement: FnWrapper) -> FnObj: ...

        def install(self) -> None: ...
