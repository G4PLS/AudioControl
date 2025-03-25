import enum
import os

from loguru import logger as log

from GtkHelper.GtkHelper import ScaleRow, BetterExpander
from GtkHelper.SearchComboRow import SearchComboRow, SearchComboRowItem
from ..actions.DeviceBase import DeviceBase
from ..internal.AdwGrid import AdwGrid

from ..internal.PulseHelpers import get_device, mute, change_volume, set_volume, get_volumes_from_device, \
    get_standard_device

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GObject

class Behaviour(enum.StrEnum):
    MUTE = "mute",
    SET = "set_volume"

class BehaviourItems(SearchComboRowItem):
    def __init__(self, display_label, behaviour):
        super().__init__(display_label)
        self._behaviour = behaviour

    @GObject.Property
    def behaviour(self):
        return self._behaviour

class DialController(DeviceBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.plugin_base.connect_to_event(event_id="com_gapls_AudioControl::PulseEvent",
                                          callback=self.on_pulse_device_change)

        self.behaviour = Behaviour.MUTE

        self.volume_adjust: int = 1
        self.volume_bounds: int = 100

        self.volume: int = 0
        self.extend_volume: bool = False

        self.is_muted: bool = False

        self.behaviour_items = [
            BehaviourItems("Mute", Behaviour.MUTE),
            BehaviourItems("Set Volume", Behaviour.SET)
        ]

    def on_ready(self):
        super().on_ready()
        self.update_mute_image()

    def build_ui(self, ui: Adw.PreferencesGroup = None) -> Adw.PreferencesGroup:
        self.ui = super().build_ui()

        self.volume_adjust_scale = ScaleRow(title=self.translate("adjust-vol-scale"), value=0, min=-50, max=50, step=1, text_left="-50",
                                            text_right="50")
        self.volume_adjust_scale.scale.set_draw_value(True)
        self.volume_adjust_scale.scale.set_size_request(100, 30)

        self.volume_bound_scale = ScaleRow(title=self.translate("adjust-bound-scale"), value=100, min=0, max=150, step=1, text_left="0",
                                           text_right="150")
        self.volume_bound_scale.scale.set_draw_value(True)
        self.volume_bound_scale.scale.set_size_request(100, 30)

        self.settings_grid.add_widget(self.volume_adjust_scale, 0, 3)
        self.settings_grid.add_widget(self.volume_bound_scale, 1, 3)

        self.ui.add(self._build_behaviour_group())
        self._create_set_volume_ui()

        self.behaviour_expander.add_row(self.set_volume_grid)

        return self.ui

    def _build_behaviour_group(self):
        behaviour_group = Adw.PreferencesGroup(title=self.translate("dial-behaviour-group"))

        self.behaviour_expander = BetterExpander(title=self.translate("dial-behaviour-extender"))
        behaviour_group.add(self.behaviour_expander)

        self.behaviour_dropdown = SearchComboRow(title=self.translate("dial-behaviour-dropdown"), use_single_line=True)
        self.behaviour_dropdown.populate(self.behaviour_items)

        self.behaviour_expander.add_row(self.behaviour_dropdown)

        return behaviour_group

    def _create_set_volume_ui(self):
        self.extend_volume_toggle = Adw.SwitchRow(title=self.translate("set-extend-toggle"))

        self.volume_scale = ScaleRow(title=self.translate("set-vol-scale"), value=0, min=0, max=100, step=1, text_left="0", text_right="100")
        self.volume_scale.scale.set_draw_value(True)
        self.volume_scale.scale.set_size_request(100, 30)

        self.set_volume_grid = AdwGrid()
        self.set_volume_grid.add_widget(self.extend_volume_toggle, 0, 0)
        self.set_volume_grid.add_widget(self.volume_scale, 1, 0)

        self.set_volume_grid.hide()

    #
    # BASE SETTINGS LOADER
    #

    def load_settings(self):
        super().load_settings()

        settings = self.get_settings()

        self.behaviour = Behaviour(settings.get("behaviour", Behaviour.MUTE))

        self.volume_adjust = settings.get("volume-adjust", 1)
        self.volume_bounds = settings.get("volume-bounds", 100)

        self.volume = settings.get("volume", 0)
        self.extend_volume = settings.get("volume-extend", False)

    def load_ui_settings(self):
        super().load_ui_settings()

        for i in range(len(self.behaviour_items)):
            if self.behaviour == self.behaviour_items[i].behaviour:
                self.behaviour_dropdown.set_selected_item(i)
                break

        if self.behaviour == Behaviour.MUTE:
            self.set_volume_grid.hide()
        else:
            self.set_volume_grid.show()

        self.volume_adjust_scale.scale.set_value(self.volume_adjust)
        self.volume_bound_scale.scale.set_value(self.volume_bounds)

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

        self.volume_adjust_scale.scale.connect("value-changed", self.on_volume_adjust_changed)
        self.volume_bound_scale.scale.connect("value-changed", self.on_volume_bounds_changed)

        self.behaviour_dropdown.connect("item-changed", self.on_behaviour_dropdown_changed)
        self.extend_volume_toggle.connect("notify::active", self.on_extend_volume_changed)
        self.volume_scale.scale.connect("value-changed", self.on_volume_changed)

    def disconnect_events(self):
        super().disconnect_events()
        try:
            self.volume_adjust_scale.scale.disconnect_by_func(self.on_volume_adjust_changed)
            self.volume_bound_scale.scale.disconnect_by_func(self.on_volume_bounds_changed)

            self.behaviour_dropdown.disconnect_by_func(self.on_behaviour_dropdown_changed)
            self.extend_volume_toggle.disconnect_by_func(self.on_extend_volume_changed)
            self.volume_scale.scale.disconnect_by_func(self.on_volume_changed)

        except:
            pass

    def on_volume_adjust_changed(self, *args, **kwargs):
        settings = self.get_settings()

        self.volume_adjust = self.volume_adjust_scale.scale.get_value()

        self.display_info()

        settings["volume-adjust"] = self.volume_adjust
        self.set_settings(settings)

    def on_volume_bounds_changed(self, *args, **kwargs):
        settings = self.get_settings()

        self.volume_bounds = self.volume_bound_scale.scale.get_value()

        settings["volume-bounds"] = self.volume_bounds
        self.set_settings(settings)

    def on_behaviour_dropdown_changed(self, _, item: BehaviourItems, index):
        settings = self.get_settings()

        self.behaviour = item.behaviour
        settings["behaviour"] = self.behaviour

        if self.behaviour == Behaviour.MUTE:
            self.set_volume_grid.hide()
        else:
            self.set_volume_grid.show()

        self.display_info()

        self.set_settings(settings)

    def on_extend_volume_changed(self, *args):
        settings = self.get_settings()

        self.extend_volume = self.extend_volume_toggle.get_active()

        extended_volume = 150 if self.extend_volume else 100

        self.volume_scale.adjustment.set_upper(extended_volume)
        self.volume_scale.label_right.set_label(str(extended_volume))

        if not self.extend_volume and self.volume_scale.scale.get_value() > 100:
            self.volume_scale.scale.set_value(100)

        settings["volume-extend"] = self.extend_volume
        self.set_settings(settings)

    def on_use_standard_changed(self, *args):
        super().on_use_standard_changed(*args)
        self.update_mute_image()

    def on_volume_changed(self, *args):
        settings = self.get_settings()

        self.volume = self.volume_scale.scale.get_value()

        self.display_info()

        settings["volume"] = self.volume
        self.set_settings(settings)

    def on_device_changed(self, *args, **kwargs):
        super().on_device_changed(*args, **kwargs)
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
            try:
                if self.use_standard:
                    device = get_standard_device(self.device_filter)
                else:
                    device = get_device(self.device_filter, self.pulse_device_name)
                self.is_muted = bool(device.mute)

                self.display_mute_image()
                self.display_info()
            except Exception as e:
                log.error(e)
                self.show_error(1)

    def on_dial_down(self):
        if self.pulse_device_name is None:
            self.show_error(1)
            return

        if self.behaviour == Behaviour.MUTE:
            self.mute_behaviour()
        else:
            self.set_volume_behaviour()

    def on_dial_turn(self, direction: int):
        if self.pulse_device_name is None:
            self.show_error(1)
            return

        try:
            if self.use_standard:
                device = get_standard_device(self.device_filter)
            else:
                device = get_device(self.device_filter, self.pulse_device_name)

            # Decreasing Volume
            if direction < 0:
                change_volume(device, -self.volume_adjust)
                return

            volumes = get_volumes_from_device(self.device_filter, device.name)
            if len(volumes) > 0 and volumes[0] < self.volume_bounds:
                if volumes[0] + self.volume_adjust > self.volume_bounds and direction > 0:
                    set_volume(device, self.volume_bounds)
                else:
                    change_volume(device, self.volume_adjust)
        except Exception as e:
            log.error(e)
            self.show_error(1)

    def mute_behaviour(self):
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

    def set_volume_behaviour(self):
        try:
            if self.use_standard:
                device = get_standard_device(self.device_filter)
            else:
                device = get_device(self.device_filter, self.pulse_device_name)
            set_volume(device, self.volume)
        except Exception as e:
            log.error(e)
            self.show_error(1)

    #
    # MISC
    #

    def display_adjustment(self):
        return str(self.volume_adjust)

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

    def display_mute_image(self):
        if self.is_muted:
            self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "mute.png"))
        else:
            self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "audio.png"))
