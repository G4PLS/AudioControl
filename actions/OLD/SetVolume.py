import gi

from GtkHelper.GtkHelper import ScaleRow
from ..actions.DeviceBase import DeviceBase
from ..internal.AdwGrid import AdwGrid

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk
from loguru import logger as log

from ..internal.PulseHelpers import get_device, set_volume, get_standard_device


class SetVolume(DeviceBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.plugin_base.connect_to_event(event_id="com_gapls_AudioControl::PulseEvent",
                                          callback=self.on_pulse_device_change)

        self.volume: int = 0
        self.extend_volume: bool = False

    def on_ready(self):
        super().on_ready()
        self.display_audio_image()

    def build_ui(self, ui: Adw.PreferencesGroup = None) -> Adw.PreferencesGroup:
        self.ui = super().build_ui()

        self.extend_volume_toggle = Adw.SwitchRow(title=self.translate("set-extend-toggle"))

        self.volume_scale = ScaleRow(title=self.translate("set-vol-scale"), value=0, min=0, max=100, step=1, text_left="0", text_right="100")
        self.volume_scale.scale.set_draw_value(True)
        self.volume_scale.scale.set_size_request(100, 30)


        self.settings_grid.add_widget(self.extend_volume_toggle, 0, 3)
        self.settings_grid.add_widget(self.volume_scale, 1, 3)

        return ui

    #
    # BASE SETTINGS LOADER
    #

    def load_settings(self):
        super().load_settings()

        settings = self.get_settings()
        self.volume = settings.get("volume", 0)
        self.extend_volume = settings.get("volume-extend", False)

    def load_ui_settings(self):
        super().load_ui_settings()

        self.extend_volume_toggle.set_active(self.extend_volume)

        if self.extend_volume:
            self.volume_scale.adjustment.set_upper(150)
            self.volume_scale.label_right.set_label("150")

        self.volume_scale.scale.set_value(self.volume)

    #
    # EVENTS
    #

    def connect_events(self):
        super().connect_events()

        self.extend_volume_toggle.connect("notify::active", self.on_extend_volume_changed)
        self.volume_scale.scale.connect("value-changed", self.on_volume_changed)

    def disconnect_events(self):
        super().disconnect_events()

        try:
            self.extend_volume_toggle.disconnect_by_func(self.on_extend_volume_changed)
            self.volume_scale.scale.disconnect_by_func(self.on_volume_changed)
        except:
            pass

    def on_extend_volume_changed(self, *args, **kwargs):
        settings = self.get_settings()

        self.extend_volume = self.extend_volume_toggle.get_active()

        extended_volume = 150 if self.extend_volume else 100

        self.volume_scale.adjustment.set_upper(extended_volume)
        self.volume_scale.label_right.set_label(str(extended_volume))

        if not self.extend_volume and self.volume_scale.scale.get_value() > 100:
            self.volume_scale.scale.set_value(100)

        settings["volume-extend"] = self.extend_volume
        self.set_settings(settings)

    def on_volume_changed(self, *args, **kwargs):
        settings = self.get_settings()

        self.volume = self.volume_scale.scale.get_value()

        self.display_info()

        settings["volume"] = self.volume
        self.set_settings(settings)

    def on_key_down(self):
        if None in (self.pulse_device_name, self.volume):
            self.show_error(1)
            return

        try:
            if self.use_standard:
                device = get_standard_device(self.device_filter)
            else:
                device = get_device(self.device_filter, self.pulse_device_name)
            set_volume(device, self.volume)
        except Exception as e:
            log.error(e)
            self.show_error(1)

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

    async def on_asset_manager_change(self, *args):
        if args[1] == "audio":
            self.display_audio_image()

    #
    # DISPLAY
    #

    def display_audio_image(self):
        result = self.plugin_base.asset_manager.icons.get_asset_values("audio")

        if result:
            _, render = result
            self.set_media(render)

    def display_adjustment(self):
        return self.volume