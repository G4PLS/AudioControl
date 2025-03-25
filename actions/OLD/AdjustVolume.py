import os

import gi
from gi.repository import Adw

from GtkHelper.GtkHelper import ScaleRow
from ..actions.DeviceBase import DeviceBase

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from loguru import logger as log

from ..internal.PulseHelpers import get_device, set_volume, change_volume, get_volumes_from_device, get_standard_device


class AdjustVolume(DeviceBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.plugin_base.connect_to_event(event_id="com_gapls_AudioControl::PulseEvent",
                                          callback=self.on_pulse_device_change)

        self.volume_adjust: int = 1
        self.volume_bounds: int = 100

    def build_ui(self, ui: Adw.PreferencesGroup = None) -> Adw.PreferencesGroup:
        self.ui = super().build_ui()

        self.volume_adjust_scale = ScaleRow(title=self.translate("adjust-vol-scale"), value=0, min=-50, max=50, step=1, text_left="-50", text_right="50")
        self.volume_adjust_scale.scale.set_draw_value(True)
        self.volume_adjust_scale.scale.set_size_request(100, 30)

        self.volume_bound_scale = ScaleRow(title=self.translate("adjust-bound-scale"), value=100, min=0, max=150, step=1, text_left="0", text_right="150")
        self.volume_bound_scale.scale.set_draw_value(True)
        self.volume_bound_scale.scale.set_size_request(100, 30)

        self.settings_grid.add_widget(self.volume_adjust_scale, 0, 3)
        self.settings_grid.add_widget(self.volume_bound_scale, 1, 3)

        return self.ui

    #
    # BASE SETTINGS LOADER
    #

    def load_settings(self):
        super().load_settings()

        settings = self.get_settings()

        self.volume_adjust = settings.get("volume-adjust", 1)
        self.volume_bounds = settings.get("volume-bounds", 100)
        self.display_icon()

    def load_ui_settings(self):
        super().load_ui_settings()

        self.volume_adjust_scale.scale.set_value(self.volume_adjust)
        self.volume_bound_scale.scale.set_value(self.volume_bounds)

    #
    # EVENTS
    #

    def connect_events(self):
        super().connect_events()

        self.volume_adjust_scale.scale.connect("value-changed", self.on_volume_adjust_changed)
        self.volume_bound_scale.scale.connect("value-changed", self.on_volume_bounds_changed)

    def disconnect_events(self):
        super().disconnect_events()
        try:
            self.volume_adjust_scale.scale.disconnect_by_func(self.on_volume_adjust_changed)
            self.volume_bound_scale.scale.disconnect_by_func(self.on_volume_bounds_changed)
        except:
            pass

    def on_volume_adjust_changed(self, *args, **kwargs):
        settings = self.get_settings()

        self.volume_adjust = self.volume_adjust_scale.scale.get_value()

        self.display_info()
        self.display_icon()

        settings["volume-adjust"] = self.volume_adjust
        self.set_settings(settings)

    def on_volume_bounds_changed(self, *args, **kwargs):
        settings = self.get_settings()

        self.volume_bounds = self.volume_bound_scale.scale.get_value()

        settings["volume-bounds"] = self.volume_bounds
        self.set_settings(settings)

    def on_key_down(self):
        if None in (self.pulse_device_name, self.volume_adjust):
            self.show_error(1)
            return

        try:
            if self.use_standard:
                device = get_standard_device(self.device_filter)
            else:
                device = get_device(self.device_filter, self.pulse_device_name)

            if self.volume_adjust < 0:
                change_volume(device, self.volume_adjust)
                return

            volumes = get_volumes_from_device(self.device_filter, device.name)

            if len(volumes) > 0 and volumes[0] < self.volume_bounds:
                if volumes[0] + self.volume_adjust > self.volume_bounds:
                    set_volume(device, self.volume_bounds)
                else:
                    change_volume(device, self.volume_adjust)
        except Exception as e:
            log.error(e)
            self.show_error(1)

    async def on_pulse_device_change(self, *args, **kwargs):
        if len(args) < 2:
            return

        self.display_info()

    async def on_asset_manager_change(self, *args):
        if args[1] == "vol-down" or args[1] == "vol-up":
            self.display_icon()

    #
    # DISPLAY
    #

    def display_adjustment(self):
        return str(self.volume_adjust)

    def display_icon(self):
        if self.volume_adjust is None:
            return

        if self.volume_adjust >= 0:
            result = self.plugin_base.asset_manager.icons.get_asset_values("vol-up")
        else:
            result = self.plugin_base.asset_manager.icons.get_asset_values("vol-down")

        if result:
            _, render = result
            self.set_media(render)
