from dbt.plugins.manager import dbt_hook, dbtPlugin
from dbt.plugins.manifest import PluginNodes
from dbt.plugins.contracts import PluginArtifacts


class ModdocsPlugin(dbtPlugin):

    def initialize(self) -> None:
        """
        Initialize the plugin. This is where you'd setup connections,
        load files, or perform other I/O.
        """
        print('Initializing ExamplePlugin')
        pass

    @dbt_hook
    def get_nodes(self) -> PluginNodes:
        """
        Return PluginNodes to dbt for injection into dbt's DAG.
        """
        return PluginNodes()
