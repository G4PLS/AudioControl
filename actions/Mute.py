import os

import pulsectl
from loguru import logger as log

from ..actions.DeviceActionBase import DeviceBase


class Mute(DeviceBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.plugin_base.connect_to_event(event_id="com_gapls_AudioControl::PulseEvent",
                                          callback=self.on_pulse_device_change)

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
                    device = self.get_device(self.device_filter)
                    self.display_mute_image(device.mute)
                    self.display_info()
                except:
                    self.show_error(1)

    def on_key_down(self):
        if self.pulse_device_name is None:
            self.show_error(1)
            return

        try:
            device = self.get_device(self.device_filter)

            mute_state = 1 if device.mute == 0 else 0

            self.mute(device, mute_state)
            self.display_mute_image(mute_state)
        except Exception as e:
            log.error(e)
            self.show_error(1)

    #
    # MISC
    #

    def update_mute_image(self):
        try:
            device = self.get_device(self.device_filter)
            self.display_mute_image(device.mute)
        except:
            self.show_error(1)

    #
    # DISPLAY
    #

    def display_info(self):
        volumes = self.get_volumes_from_device()
        info = ""
        if len(volumes) > 0:
            info = str(int(volumes[0]))
        self.set_bottom_label(info)

    def display_mute_image(self, mute_state):
        if mute_state == 1:
            self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "mute.png"))
        else:
            self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "audio.png"))
