from dbt.plugins.manager import dbtPlugin

from . import patches


class DbtInlineDocsPlugin(dbtPlugin):
    def initialize(self) -> None:
        for patch in patches.ALL:
            patch.install()


plugins = [DbtInlineDocsPlugin]
