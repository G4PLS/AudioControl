import os

import pulsectl
from loguru import logger as log

from ..actions.DeviceBase import DeviceBase
from ..internal.PulseHelpers import get_device, mute, get_volumes_from_device, get_standard_device


class Mute(DeviceBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.plugin_base.connect_to_event(event_id="com_gapls_AudioControl::PulseEvent",
                                          callback=self.on_pulse_device_change)
        self.is_muted: bool = False

    def on_ready(self):
        super().on_ready()
        self.update_mute_image()

    #
    # EVENTS
    #

    def on_device_changed(self, *args, **kwargs):
        super().on_device_changed(*args, **kwargs)
        self.update_mute_image()

    def on_use_standard_changed(self, *args):
        super().on_use_standard_changed(*args)
        self.update_mute_image()

    async def on_pulse_device_change(self, *args, **kwargs):
        if len(args) < 2:
            return

        event = args[1]

        if self.use_standard:
            device = get_standard_device(self.device_filter)
            index = device.index
        else:
            index = self.device_index

        if event.index == index:
            with pulsectl.Pulse("mute-event") as pulse:
                try:
                    if self.use_standard:
                        device = get_standard_device(self.device_filter)
                    else:
                        device = get_device(self.device_filter, self.pulse_device_name)
                    self.is_muted = bool(device.mute)
                    self.display_mute_image()
                    self.display_info()
                except:
                    self.show_error(1)

    def on_key_down(self):
        if self.pulse_device_name is None:
            self.show_error(1)
            return

        try:
            if self.use_standard:
                device = get_standard_device(self.device_filter)
            else:
                device = get_device(self.device_filter, self.pulse_device_name)

            self.is_muted = not device.mute
            mute(device, self.is_muted)
            self.display_mute_image()
        except Exception as e:
            log.error(e)
            self.show_error(1)

    async def on_asset_manager_change(self, *args):
        if args[1] == "mute" or args[1] == "audio":
            self.display_mute_image()

    #
    # MISC
    #

    def update_mute_image(self):
        try:
            if self.use_standard:
                device = get_standard_device(self.device_filter)
            else:
                device = get_device(self.device_filter, self.pulse_device_name)
            self.is_muted = bool(device.mute)
            self.display_mute_image()
        except:
            self.show_error(1)

    #
    # DISPLAY
    #

    def display_adjustment(self):
        if self.is_muted:
            return "Muted"
        return "Unmuted"

    def display_mute_image(self):
        if self.is_muted:
            _, render = self.plugin_base.asset_manager.icons.get_asset_values("mute")
        else:
            _, render = self.plugin_base.asset_manager.icons.get_asset_values("audio")
        self.set_media(render)