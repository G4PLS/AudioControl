# Import StreamController modules

import pulsectl
from src.backend.PluginManager.ActionHolder import ActionHolder
from src.backend.PluginManager.ActionInputSupport import ActionInputSupport
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.DeckManagement.InputIdentifier import Input

from .actions.AdjustVolume import AdjustVolume
from .actions.Mute import Mute
from .actions.SetVolume import SetVolume
from .actions.VolumeDisplay import VolumeDisplay
from .actions.DialController import DialController
from .internal.PulseEventListener import PulseEvent

from .actions.DeviceActionBase import DeviceBase


class AudioControl(PluginBase):
    def __init__(self):
        super().__init__()
        self.init_vars()

        self.t = ActionHolder(
            plugin_base=self,
            action_base=DeviceBase,
            action_id_suffix="TEST",
            action_name="TEST",
            action_support= {
                Input.Key: ActionInputSupport.SUPPORTED,
                Input.Dial: ActionInputSupport.SUPPORTED,
                Input.Touchscreen: ActionInputSupport.SUPPORTED
            }
        )
        self.add_action_holder(self.t)



        self.mute_action_holder = ActionHolder(
            plugin_base=self,
            action_base=Mute,
            action_id_suffix="Mute",
            action_name=self.lm.get("action.name.mute"),
            action_support={Input.Key: ActionInputSupport.SUPPORTED}
        )
        self.add_action_holder(self.mute_action_holder)

        # Events

        self.pulse_sink_event_holder = PulseEvent(
            self,
            "com_gapls_AudioControl::PulseEvent",
            "sink", "source"
        )
        self.add_event_holder(self.pulse_sink_event_holder)

        self.register()

        return

        self.set_volume_action_holder = ActionHolder(
            plugin_base=self,
            action_base=SetVolume,
            action_id_suffix="SetVolume",
            action_name=self.lm.get("action.name.set-volume"),
        action_support = {Input.Key: ActionInputSupport.SUPPORTED}
        )
        self.add_action_holder(self.set_volume_action_holder)

        self.adjust_volume_action_holder = ActionHolder(
            plugin_base=self,
            action_base=AdjustVolume,
            action_id_suffix="AdjustVolume",
            action_name=self.lm.get("action.name.adjust-volume"),
            action_support={Input.Key: ActionInputSupport.SUPPORTED}
        )
        self.add_action_holder(self.adjust_volume_action_holder)

        self.volume_display_action_holder = ActionHolder(
            plugin_base=self,
            action_base=VolumeDisplay,
            action_id_suffix="VolumeDisplay",
            action_name=self.lm.get("action.name.volume-display"),
            action_support={Input.Key: ActionInputSupport.SUPPORTED}
        )
        self.add_action_holder(self.volume_display_action_holder)

        self.dial_controller_action_holder = ActionHolder(
            plugin_base=self,
            action_base=DialController,
            action_id_suffix="DialController",
            action_name=self.lm.get("action.name.dial-controller"),
            action_support={Input.Dial: ActionInputSupport.UNTESTED}
        )
        self.add_action_holder(self.dial_controller_action_holder)

        # Events

        self.pulse_sink_event_holder = PulseEvent(
            self,
            "com_gapls_AudioControl::PulseEvent",
            "sink", "source"
        )
        self.add_event_holder(self.pulse_sink_event_holder)

        self.register()

    def init_vars(self):
        self.lm = self.locale_manager
        self.pulse = pulsectl.Pulse("audio-control-main")
