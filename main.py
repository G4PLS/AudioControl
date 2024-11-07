# Import StreamController modules
import os.path

import pulsectl

from locales.LocaleManager import LocaleManager
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


class AudioControl(PluginBase):
    def __init__(self):
        super().__init__()
        self.init_vars()

        self.mute_action_holder = ActionHolder(
            plugin_base=self,
            action_base=Mute,
            action_id_suffix="Mute",
            action_name=self.lm.get("name-mute"),
            action_support={Input.Key: ActionInputSupport.SUPPORTED}
        )
        self.add_action_holder(self.mute_action_holder)

        self.set_volume_action_holder = ActionHolder(
            plugin_base=self,
            action_base=SetVolume,
            action_id_suffix="SetVolume",
            action_name=self.lm.get("name-set-vol"),
            action_support={Input.Key: ActionInputSupport.SUPPORTED}
        )
        self.add_action_holder(self.set_volume_action_holder)

        self.adjust_volume_action_holder = ActionHolder(
            plugin_base=self,
            action_base=AdjustVolume,
            action_id_suffix="AdjustVolume",
            action_name=self.lm.get("name-adjust-vol"),
            action_support={Input.Key: ActionInputSupport.SUPPORTED}
        )
        self.add_action_holder(self.adjust_volume_action_holder)

        self.volume_display_action_holder = ActionHolder(
            plugin_base=self,
            action_base=VolumeDisplay,
            action_id_suffix="VolumeDisplay",
            action_name=self.lm.get("name-vol-display"),
            action_support={Input.Key: ActionInputSupport.SUPPORTED}
        )
        self.add_action_holder(self.volume_display_action_holder)

        self.dial_controller_action_holder = ActionHolder(
            plugin_base=self,
            action_base=DialController,
            action_id_suffix="DialController",
            action_name=self.lm.get("name-dial"),
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
        self.lm = LocaleManager(os.path.join(self.PATH, "locales.csv"))
        self.pulse = pulsectl.Pulse("audio-control-main")