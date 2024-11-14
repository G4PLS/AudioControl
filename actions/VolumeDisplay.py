from ..actions.DeviceBase import DeviceBase
from ..internal.PulseHelpers import get_standard_device

class VolumeDisplay(DeviceBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.plugin_base.connect_to_event(event_id="com_gapls_AudioControl::PulseEvent",
                                          callback=self.on_pulse_device_change)

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
            try:
                self.display_info()
            except:
                self.show_error(1)