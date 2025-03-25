import enum
from dataclasses import dataclass

from GtkHelper.GenerativeUI.EntryRow import EntryRow
from GtkHelper.GenerativeUI.SwitchRow import SwitchRow
from GtkHelper.GenerativeUI.ToggleRow import ToggleRow
from GtkHelper.GtkHelper import BetterExpander
from ..internal.AdwGrid import AdwGrid
from ..internal.PulseHelpers import DeviceFilter, get_device_list, filter_proplist, get_volumes_from_device, \
    get_standard_device
from src.backend.PluginManager.ActionCore import ActionCore
from src.backend.PluginManager.EventAssigner import EventAssigner
from src.backend.DeckManagement.InputIdentifier import InputEvent, Input

import gi
from gi.repository import Adw

from GtkHelper.GenerativeUI.ComboRow import ComboRow
from GtkHelper.ComboRow import SimpleComboRowItem, BaseComboRowItem

class InfoContent(enum.Enum):
    VOLUME = SimpleComboRowItem("volume", "Volume")
    ADJUSTMENT = SimpleComboRowItem("adjustment", "Adjustment")

class Device(BaseComboRowItem):
    def __init__(self, pulse_name, pulse_index, device_name):
        super().__init__()
        self.pulse_name: str = pulse_name
        self.pulse_index: int = pulse_index
        self.device_name: str = device_name

    def __str__(self):
        return self.device_name

    def get_value(self):
        return self.pulse_name

class AudioCore(ActionCore):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_configuration = True

        self.plugin_base.asset_manager.icons.add_listener(self.icon_changed)

        # Settings

        self.selected_device: Device = None

        self.device_filter: DeviceFilter = None
        self.info_content = None

        self.show_device_name = None
        self.device_nick = None

        self.show_info_content = None
        self.info_content = None

        self.use_standard_device = None

        self.loaded_devices: list[Device] = []

        # Icon

        self.icon_keys = []
        self._current_icon = None
        self._icon_name = ""

    def create_generative_ui(self):
        self.standard_device_switch = SwitchRow(
            action_core=self,
            var_name="device.use-standard",
            default_value=False,
            title="Standard Device",
            auto_add=False,
            complex_var_name=True,
            on_change=self.show_standard_device_changed
        )

        self.device_filter_combo_row = ComboRow(
            action_core=self,
            var_name="device.filter",
            default_value=DeviceFilter.SINK.value,
            items=[DeviceFilter.SINK.value, DeviceFilter.SOURCE.value],
            title="base-filter-dropdown",
            auto_add=False,
            complex_var_name=True,
            on_change=self.device_filter_changed
        )

        self.device_combo_row = ComboRow(
            action_core=self,
            var_name="device.pulse-name",
            default_value="",
            items=[],
            title="base-device-dropdown",
            auto_add=False,
            complex_var_name=True,
            on_change=self.device_changed
        )

        # Use Standard Device Toggle/Switch

        self.info_content_switch = SwitchRow(
            action_core=self,
            var_name="info-content.visible",
            default_value=True,
            title="base-info-toggle",
            auto_add=False,
            complex_var_name=True,
            on_change=self.show_info_content_changed
        )

        self.info_content_combo_row = ComboRow(
            action_core=self,
            var_name="info-content.type",
            default_value=InfoContent.VOLUME.value,
            items=[InfoContent.VOLUME.value, InfoContent.ADJUSTMENT.value],
            title="base-info-content",
            auto_add=False,
            complex_var_name=True,
            on_change=self.info_content_changed
        )

        self.device_name_switch = SwitchRow(
            action_core=self,
            var_name="show-device-name",
            default_value=True,
            title="base-name-toggle",
            auto_add=False,
            on_change=self.show_device_nick_changed
        )

        self.device_nick_entry = EntryRow(
            action_core=self,
            var_name="device.nick",
            default_value="",
            title="base-nick",
            auto_add=False,
            complex_var_name=True,
            on_change=self.device_nick_changed
        )

        self.device_filter = self.device_filter_combo_row.get_selected_item()

    def get_config_rows(self) -> "list[Adw.PreferencesRow]":
        self.standard_device_switch.unparent()
        self.device_filter_combo_row.unparent()
        self.device_combo_row.unparent()
        self.info_content_switch.unparent()
        self.info_content_combo_row.unparent()
        self.device_name_switch.unparent()
        self.device_nick_entry.unparent()

        device_expander = BetterExpander(title="Device")

        device_expander.add_row(self.standard_device_switch.widget)
        device_expander.add_row(self.device_filter_combo_row.widget)
        device_expander.add_row(self.device_combo_row.widget)

        info_expander = BetterExpander(title="Info")

        info_expander.add_row(self.info_content_switch.widget)
        info_expander.add_row(self.info_content_combo_row.widget)

        device_name_expander = BetterExpander(title="Device Name")

        device_name_expander.add_row(self.device_name_switch.widget)
        device_name_expander.add_row(self.device_nick_entry.widget)

        self.load_devices()

        return [device_expander, info_expander, device_name_expander]

    def on_ready(self):
        self.load_devices()
        self.set_current_icon()

    def on_tick(self):
        self.check_standard_device()

    def load_devices(self):
        device_list = get_device_list(self.device_filter)

        self.loaded_devices = []

        for device in device_list:
            if device.description.__contains__("Monitor"):
                continue

            device_name = filter_proplist(device.proplist)

            if device_name is None:
                continue

            self.loaded_devices.append(Device(
                pulse_name=device.name,
                pulse_index=device.index,
                device_name=device_name
            ))

        self.device_combo_row.populate(self.loaded_devices, self.device_combo_row.get_value())
        self.display_device_info()

    # UI Events

    def show_standard_device_changed(self, widget, value, old):
        print(self.__class__.__name__)
        self.use_standard_device = value
        self.device_combo_row.widget.set_sensitive(not self.use_standard_device)
        self.check_standard_device()

    def device_filter_changed(self, widget, value, old):
        self.device_filter = value
        self.load_devices()

    def device_changed(self, widget, value, old):
        self.selected_device = value
        self.display_device_name()
        self.display_device_info()

    def show_info_content_changed(self, widget, value, old):
        self.show_info_content = value
        self.display_device_info()

    def info_content_changed(self, widget, value, old):
        self.info_content = value
        self.display_device_info()

    def show_device_nick_changed(self, widget, value, old):
        self.show_device_name = value
        self.display_device_name()

    def device_nick_changed(self, widget, value, old):
        self.device_nick = value
        self.display_device_name()

    ############ DISPLAY #############

    def display_device_name(self):
        if not self.show_device_name:
            self.set_top_label("")
            return

        if self.device_nick and self.device_nick != "":
            self.set_top_label(self.device_nick)
        else:
            self.set_top_label(self.selected_device.device_name)

    def display_device_info(self):
        if not self.show_info_content:
            self.set_bottom_label("")
            return

        if self.info_content == InfoContent.VOLUME.value:
            self.set_bottom_label(self.display_volume())
        elif self.info_content == InfoContent.ADJUSTMENT.value:
            self.set_bottom_label(self.display_adjustment())
        else:
            self.set_bottom_label("")

    def display_volume(self):
        volumes = get_volumes_from_device(self.device_filter, self.selected_device.pulse_name)

        if len(volumes) > 0:
            return str(int(volumes[0]))
        return "N/A"

    def display_adjustment(self):
        pass

    async def icon_changed(self, event: str, key: str, asset):
        if not key in self.icon_keys:
            return

        if key != self._icon_name:
            return

        self._current_icon = asset
        self._icon_name = key

        self.display_icon()

    def display_icon(self):
        if not self._current_icon:
            return

        _, rendered = self._current_icon.get_values()

        if rendered or None:
            self.set_media(image=rendered)

    def set_current_icon(self):
        pass

    def check_standard_device(self):
        if self.use_standard_device:
            standard_device = get_standard_device(self.device_filter)

            if self.selected_device.pulse_name == standard_device.name:
                return

            for device in self.loaded_devices:
                if device.pulse_name != standard_device.name:
                    continue

                self.selected_device = device
                self.device_combo_row.set_selected_item(device)
                break