# Import StreamController modules
import os.path

import pulsectl

from src.backend.PluginManager.ActionHolder import ActionHolder
from src.backend.PluginManager.ActionInputSupport import ActionInputSupport
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.DeckManagement.InputIdentifier import Input



from .internal.PulseEventListener import PulseEvent
from .actions.AudioCore import AudioCore

from .actions.Mute import Mute
from .actions.SetVolume import SetVolume
from .actions.AdjustVolume import AdjustVolume

from .globals import Icons

class AudioControl(PluginBase):
    def __init__(self):
        super().__init__(use_legacy_locale=False)
        self.init_vars()

        self.has_plugin_settings = True

        self.test = ActionHolder(
            plugin_base=self,
            action_core=AudioCore,
            action_id_suffix="AudioCore",
            action_name="AudioCore",
            action_support= {
                Input.Key: ActionInputSupport.SUPPORTED,
                Input.Dial: ActionInputSupport.SUPPORTED,
                Input.Touchscreen: ActionInputSupport.SUPPORTED
            }
        )
        self.add_action_holder(self.test)

        self.mute = ActionHolder(
            plugin_base=self,
            action_core=Mute,
            action_id_suffix="Mute",
            action_name="Mute",
            action_support= {
                Input.Key: ActionInputSupport.SUPPORTED,
                Input.Dial: ActionInputSupport.UNTESTED,
                Input.Touchscreen: ActionInputSupport.UNTESTED
            }
        )
        self.add_action_holder(self.mute)

        self.set_volume = ActionHolder(
            plugin_base=self,
            action_core=SetVolume,
            action_id_suffix="SetVolume",
            action_name="Set Volume",
            action_support= {
                Input.Key: ActionInputSupport.SUPPORTED,
                Input.Dial: ActionInputSupport.UNTESTED,
                Input.Touchscreen: ActionInputSupport.UNTESTED
            }
        )
        self.add_action_holder(self.set_volume)

        self.volume_adjust = ActionHolder(
            plugin_base=self,
            action_core=AdjustVolume,
            action_id_suffix="AdjustVolume",
            action_name="Adjust Volume",
            action_support={
                Input.Key: ActionInputSupport.SUPPORTED,
                Input.Dial: ActionInputSupport.UNTESTED,
                Input.Touchscreen: ActionInputSupport.UNTESTED
            }
        )
        self.add_action_holder(self.volume_adjust)

        # Events

        self.pulse_sink_event_holder = PulseEvent(
            self,
            "com_gapls_AudioControl::PulseEvent",
            pulsectl.PulseEventMaskEnum.sink,
            pulsectl.PulseEventMaskEnum.source
        )
        self.add_event_holder(self.pulse_sink_event_holder)

        self.register()

    def init_vars(self):
        self.pulse = pulsectl.Pulse("audio-control-main")

        self.add_icon(Icons.MUTED, self.get_asset_path("mute.png"))
        self.add_icon(Icons.UNMUTED, self.get_asset_path("audio.png"))
        self.add_icon(Icons.VOLUME_DOWN, self.get_asset_path("vol_down.png"))
        self.add_icon(Icons.VOLUME_UP, self.get_asset_path("vol_up.png"))