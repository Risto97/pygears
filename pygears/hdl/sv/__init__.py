from pygears.conf import PluginBase, safe_bind
from .generate import svgen_generate
from .inst import svgen_inst
from .svmod import SVModuleGen
from pygears.conf import PluginBase, config


class SVGenPlugin(PluginBase):
    @classmethod
    def bind(cls):
        safe_bind('svgen/flow', [svgen_inst, svgen_generate])
        safe_bind('svgen/module_namespace', {})
        safe_bind('svgen/module_namespace/Gear', SVModuleGen)
        safe_bind('svgen/module_namespace/GearHierRoot', SVModuleGen)


from pygears.conf import load_plugin_folder
import os
load_plugin_folder(os.path.join(os.path.dirname(__file__), 'modules'))

__all__ = ['svgen_generate']
