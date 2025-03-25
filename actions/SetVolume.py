from GtkHelper.GenerativeUI.ScaleRow import ScaleRow
from GtkHelper.GenerativeUI.SwitchRow import SwitchRow
from src.backend.PluginManager.ActionCore import ActionCore
from src.backend.DeckManagement.InputIdentifier import InputEvent, Input
from src.backend.PluginManager.PluginSettings.Asset import Color, Icon
from src.backend.PluginManager.EventAssigner import EventAssigner
from .AudioCore import AudioCore

from ..globals import Icons

from GtkHelper.GtkHelper import better_disconnect

import gi

from ..internal.PulseHelpers import set_volume

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw


class SetVolume(AudioCore):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Setup AssetManager values
        self.icon_keys = [Icons.UNMUTED]
        self._icon_name = Icons.UNMUTED
        self._current_icon = self.get_icon(Icons.UNMUTED)

        self.extend_volume: bool = None
        self.volume: int = None

        # Setup Action Related Stuff
        self.create_event_assigners()
        self.create_generative_ui()

    def create_generative_ui(self):
        super().create_generative_ui()

        self.extend_volume_switch = SwitchRow(
            action_core=self,
            var_name="volume.extend",
            default_value=False,
            title="extend-volume",
            complex_var_name=True,
            on_change=self.extend_volume_changed
        )

        self.volume_scale = ScaleRow(
            action_core=self,
            var_name="volume.value",
            default_value=50,
            min=0,
            max=100,
            title="volume",
            step=1,
            digits=0,
            draw_value=True,
            add_text_entry=True,
            text_entry_max_length=4,
            complex_var_name=True,
            on_change=self.volume_scale_changed
        )

    def create_event_assigners(self):
        self.event_manager.add_event_assigner(
            EventAssigner(
                id="set_volume",
                ui_label="Set Volume",
                default_event=Input.Key.Events.DOWN,
                callback=self.on_set_volume
            )
        )

    def on_ready(self):
        super().on_ready()
        self.display_icon()
        self.display_device_info()
        self.display_device_name()

    def volume_scale_changed(self, widget, value, old):
        self.volume = int(value)

    def extend_volume_changed(self, widget, value, old):
        self.extend_volume = value

        if self.extend_volume:
            self.volume_scale.max = 150
        else:
            self.volume_scale.max = 100

    def on_set_volume(self, *args):
        if self.selected_device is None:
            self.show_error(1)
            return

        set_volume(self.device_filter, self.selected_device.pulse_name, self.volume)

    def display_adjustment(self):
        return "B"