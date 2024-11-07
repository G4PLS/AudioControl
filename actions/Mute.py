import os

import pulsectl
from loguru import logger as log

from ..actions.DeviceBase import DeviceBase
from ..internal.PulseHelpers import get_device, mute, get_volumes_from_device


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

    async def on_pulse_device_change(self, *args, **kwargs):
        if len(args) < 2:
            return

        event = args[1]

        if event.index == self.device_index:
            with pulsectl.Pulse("mute-event") as pulse:
                try:
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
            device = get_device(self.device_filter, self.pulse_device_name)

            self.is_muted = not device.mute
            mute(device, self.is_muted)
            self.display_mute_image()
        except Exception as e:
            log.error(e)
            self.show_error(1)

    #
    # MISC
    #

    def update_mute_image(self):
        try:
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
            self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "mute.png"))
        else:
            self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "audio.png"))
