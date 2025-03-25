from src.backend.DeckManagement.InputIdentifier import Input
from .AudioCore import AudioCore
from src.backend.PluginManager.EventAssigner import EventAssigner
from ..internal.PulseHelpers import get_device, mute
from loguru import logger as log
import pulsectl

from ..globals import Icons

class Mute(AudioCore):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.icon_keys = [Icons.MUTED, Icons.UNMUTED]

        self.event_manager.add_event_assigner(
            EventAssigner(
                id="mute",
                ui_label="Mute",
                default_event=Input.Key.Events.DOWN,
                callback=self.on_mute
            ))

        self.plugin_base.connect_to_event(event_id="com_gapls_AudioControl::PulseEvent",
                                          callback=self.on_pulse_device_change)

        self.is_muted = False

        self.create_generative_ui()

    def on_ready(self):
        super().on_ready()
        self.update_mute_image()

    def on_mute(self, event):
        if self.selected_device is None:
            self.show_error(1)
            return

        try:
            device = get_device(self.device_filter_combo_row.get_selected_item(), self.selected_device.pulse_name)
            self.mute(device)
        except Exception as e:
            self.show_error(1)

    ########### UI STUFF ###########

    def update_mute_image(self):
        with pulsectl.Pulse("mute-event") as pulse:
            try:
                device = get_device(self.device_filter_combo_row.get_selected_item(), self.selected_device.pulse_name)
                self.is_muted = bool(device.mute)

                self.set_current_icon()
                self.display_device_info()
            except Exception as e:
                self.show_error(1)

    def mute(self, device):
        self.is_muted = not device.mute

        self.set_current_icon()

        mute(device, self.is_muted)

    def set_current_icon(self):
        if self.is_muted:
            self._current_icon = self.get_icon(Icons.MUTED)
            self._icon_name = Icons.MUTED
        else:
            self._current_icon = self.get_icon(Icons.UNMUTED)
            self._icon_name = Icons.UNMUTED

        self.display_icon()

    async def on_pulse_device_change(self, *args, **kwargs):
        if len(args) < 2:
            return

        event = args[1]
        index = self.selected_device.pulse_index

        if event.index == index:
            self.update_mute_image()

    def display_adjustment(self):
        if self.is_muted:
            return "Muted"
        return "Unmuted"