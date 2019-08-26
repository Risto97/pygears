from pygears.conf import PluginBase, safe_bind
from .generate import vgen_generate
from .inst import vgen_inst
from .vmod import VModuleInst
from pygears.conf import PluginBase, config

from .vcompile import compile_gear, compile_gear_body


class VGenPlugin(PluginBase):
    @classmethod
    def bind(cls):
        safe_bind('vgen/flow', [vgen_inst, vgen_generate])
        # safe_bind('vgen/flow', [vgen_inst])
        safe_bind('vgen/module_namespace', {})
        safe_bind('vgen/module_namespace/Gear', VModuleInst)
        safe_bind('vgen/module_namespace/GearHierRoot', VModuleInst)


from pygears.conf import load_plugin_folder
import os
load_plugin_folder(os.path.join(os.path.dirname(__file__), 'modules'),
                   package='pygears.hdl.v')

__all__ = ['compile_gear', 'compile_gear_body']
