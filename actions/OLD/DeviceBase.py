import enum

import gi
import pulsectl

from src.backend.DeckManagement.InputIdentifier import InputEvent, Input
from src.backend.PluginManager.ActionBase import ActionBase

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GObject, Gtk

from loguru import logger as log

from ..internal.PulseHelpers import get_device_list, filter_proplist, DeviceFilter, get_device, get_volumes_from_device, get_standard_device

from GtkHelper.SearchComboRow import SearchComboRow, SearchComboRowItem
from ..internal.AdwGrid import AdwGrid
from ..internal.AssetManager.AssetManagerWindow import Window

class InfoContent(enum.StrEnum):
    VOLUME = "volume",
    ADJUSTMENT = "adjustment",


class DeviceFilterItem(SearchComboRowItem):
    def __init__(self, display_label, filter: DeviceFilter):
        super().__init__(display_label)
        self._pulse_filter = filter

    @GObject.Property
    def pulse_filter(self):
        return self._pulse_filter


class InfoContentItem(SearchComboRowItem):
    def __init__(self, display_label, info_content: InfoContent):
        super().__init__(display_label)
        self._info_content = info_content

    @GObject.Property
    def info_content(self):
        return self._info_content


class DeviceBase(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_configuration = True

        # Internal
        self.pulse_device_name: str = ""  # Actual name of the Pulse Device
        self.device_index: int = None  # Index of the Device
        self.asset_manager_window = None

        # Settings
        # Device Selection
        self.device_filter: DeviceFilter = DeviceFilter.SINK  # Filter for displaying devices for said filter
        self.device_name: str = ""  # Device Name after filtering proplist
        self.use_standard: bool = False

        # Info Display
        self.show_info: bool = False  # Toggle to show info
        self.info_content: InfoContent = InfoContent.VOLUME  # Type of info to show

        # Device Display
        self.show_device_name: bool = False  # If you should show the device name
        self.device_nick: str = None  # A nick for any given device

        self.plugin_base.asset_manager.icons.add_listener(self.on_asset_manager_change)

    #
    # UI
    #

    def get_custom_config_area(self):
        self.build_ui()
        self.load_ui_settings()
        self.connect_events()

        return self.ui

    def build_ui(self, ui: Adw.PreferencesGroup = None) -> Adw.PreferencesGroup:
        self.ui = ui or Adw.PreferencesGroup()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        settings_group = Adw.PreferencesGroup()

        self.asset_manager_button = Gtk.Button(label="Open Asset Manager")

        self.settings_grid = AdwGrid()

        # Add Device Row
        self.device_filter_dropdown = SearchComboRow(self.translate("base-filter-dropdown"), use_single_line=True, hexpand=True)
        self.device_dropdown = SearchComboRow(self.translate("base-device-dropdown"), use_single_line=True, hexpand=True)
        self.use_standard_toggle = Adw.SwitchRow()
        self.use_standard_toggle.set_tooltip_text("Use Standard Device and Ignore selected Device")

        self.device_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.device_box.append(self.device_dropdown)
        self.device_box.append(self.use_standard_toggle)

        # Add Info Row
        self.info_toggle = Adw.SwitchRow(title=self.translate("base-info-toggle"), hexpand=True)
        self.info_content_dropdown = SearchComboRow(self.translate("base-info-content"), use_single_line=True, hexpand=True)

        # Add Name Row
        self.device_name_toggle = Adw.SwitchRow(title=self.translate("base-name-toggle"), hexpand=True)
        self.device_nick_entry = Adw.EntryRow(title=self.translate("base-nick"), hexpand=True)

        self.settings_grid.add_widget(self.device_filter_dropdown, 0, 0)
        self.settings_grid.add_widget(self.device_box, 1, 0)

        self.settings_grid.add_widget(self.info_toggle, 0, 1)
        self.settings_grid.add_widget(self.info_content_dropdown, 1, 1)

        self.settings_grid.add_widget(self.device_name_toggle, 0, 2)
        self.settings_grid.add_widget(self.device_nick_entry, 1, 2)

        settings_group.add(self.settings_grid)

        box.append(self.asset_manager_button)
        box.append(settings_group)

        self.ui.add(box)

        return self.ui

    #
    # SETTINGS
    #

    def load_settings(self):
        settings = self.get_settings()

        self.pulse_device_name = settings.get("pulse-name", None)

        self.device_filter = DeviceFilter(settings.get("device-filter", DeviceFilter.SINK))
        self.device_name = settings.get("device-name", None)
        self.use_standard = settings.get("use-standard", False)

        self.show_info = settings.get("show-info", False)
        self.info_content = InfoContent(settings.get("info-content", InfoContent.VOLUME))

        self.show_device_name = settings.get("show-device-name", False)
        self.device_nick = settings.get("nick", None)

        device = None

        if self.use_standard:
            device = get_standard_device(self.device_filter)
        elif self.pulse_device_name:
            device = get_device(self.device_filter, self.pulse_device_name)
        else:
            for audio_device in get_device_list(self.device_filter):
                if audio_device.description.__contains__("Monitor"):
                    continue

                device = audio_device
                break

        if not device:
            return

        self.device_index = device.index
        self.device_name = filter_proplist(device.proplist)
        self.pulse_device_name = device.name

    def load_ui_settings(self):
        self.disconnect_events()

        self.load_device_filter()
        self.load_device()
        self.load_info_content()

        self.info_toggle.set_active(self.show_info)
        self.device_name_toggle.set_active(self.show_device_name)
        self.use_standard_toggle.set_active(self.use_standard)

        self.device_nick_entry.set_text(self.device_nick or "")

        self.connect_events()

    def load_device_filter(self):
        items = [
            DeviceFilterItem("Sink", DeviceFilter.SINK),
            DeviceFilterItem("Source", DeviceFilter.SOURCE)
        ]

        self.device_filter_dropdown.populate(items)

        for i in range(len(items)):
            if items[i].pulse_filter == self.device_filter:
                self.device_filter_dropdown.set_selected_item(i)
                break

    def load_device(self):
        device_list = []

        for device in get_device_list(self.device_filter):
            if device.description.__contains__("Monitor"):
                continue

            device_name = filter_proplist(device.proplist)

            if device_name is not None:
                device_list.append(SearchComboRowItem(display_label=device_name))

        self.device_dropdown.populate(device_list)

        for i in range(len(device_list)):
            if device_list[i].display_label == self.device_name:
                self.device_dropdown.set_selected_item(i)
                break

    def load_info_content(self):
        items = [
            InfoContentItem("Volume", InfoContent.VOLUME),
            InfoContentItem("Adjustment", InfoContent.ADJUSTMENT)
        ]

        self.info_content_dropdown.populate(items)

        for i in range(len(items)):
            if items[i].info_content == self.info_content:
                self.info_content_dropdown.set_selected_item(i)
                break

    #
    # UI EVENTS
    #

    def connect_events(self):
        self.asset_manager_button.connect("clicked", self.on_asset_manager_button_clicked)

        self.device_filter_dropdown.connect("item-changed", self.on_device_filter_changed)
        self.device_dropdown.connect("item-changed", self.on_device_changed)
        self.use_standard_toggle.connect("notify::active", self.on_use_standard_changed)

        self.info_toggle.connect("notify::active", self.on_info_toggle_changed)
        self.info_content_dropdown.connect("item-changed", self.on_info_content_changed)

        self.device_name_toggle.connect("notify::active", self.on_device_name_toggle_changed)
        self.device_nick_entry.connect("changed", self.on_device_nick_changed)

    def disconnect_events(self):
        try:
            self.device_filter_dropdown.disconnect_by_func(self.on_device_filter_changed)
            self.device_dropdown.disconnect_by_func(self.on_device_changed)
            self.use_standard_toggle.disconnect_by_func(self.on_use_standard_changed)

            self.info_toggle.disconnect_by_func(self.on_info_toggle_changed)
            self.info_content_dropdown.disconnect_by_func(self.on_info_content_changed)

            self.device_name_toggle.disconnect_by_func(self.on_device_name_toggle_changed)
            self.device_nick_entry.disconnect_by_func(self.on_device_nick_changed)
        except:
            pass

    def on_asset_manager_button_clicked(self, *args):
        if self.asset_manager_window is None:
            self.create_asset_manager_window()
            self.asset_manager_window.present()

    def on_device_filter_changed(self, _, item: DeviceFilterItem, index):
        settings = self.get_settings()

        self.device_filter = item.pulse_filter
        self.pulse_device_name = None

        self.load_device()
        self.display_device_name()
        self.display_info()

        settings["device-filter"] = self.device_filter
        self.set_settings(settings)

    def on_device_changed(self, _, item: SearchComboRowItem, index):
        settings = self.get_settings()

        self.device_name = item.display_label

        self.set_device_settings()

        self.display_device_name()
        self.display_info()

        settings["pulse-name"] = self.pulse_device_name
        self.set_settings(settings)

    def on_use_standard_changed(self, *args):
        settings = self.get_settings()

        self.use_standard = self.use_standard_toggle.get_active()

        self.display_device_name()
        self.display_info()

        settings["use-standard"] = self.use_standard
        self.set_settings(settings)

    def on_info_toggle_changed(self, *args):
        settings = self.get_settings()

        self.show_info = self.info_toggle.get_active()
        self.display_info()

        settings["show-info"] = self.show_info
        self.set_settings(settings)

    def on_info_content_changed(self, _, item: InfoContentItem, index):
        settings = self.get_settings()

        self.info_content = item.info_content
        settings["info-content"] = self.info_content

        self.display_info()

        self.set_settings(settings)

    def on_device_name_toggle_changed(self, *args):
        settings = self.get_settings()

        self.show_device_name = self.device_name_toggle.get_active()
        settings["show-device-name"] = self.show_device_name

        self.display_device_name()

        self.set_settings(settings)

    def on_device_nick_changed(self, *args):
        settings = self.get_settings()

        nick = self.device_nick_entry.get_text()

        if len(nick) > 0:
            self.device_nick = nick
        else:
            self.device_nick = None

        self.display_device_name()

        settings["nick"] = self.device_nick
        self.set_settings(settings)

    async def on_asset_manager_change(self, *args):
        pass

    #
    # ACTION EVENTS
    #

    def on_ready(self):
        self.load_settings()
        self.display_device_name()
        self.display_info()

    def event_callback(self, event: InputEvent, data: dict = None):
        if event == Input.Key.Events.SHORT_UP:
            self.on_key_down()
        elif event == Input.Key.Events.HOLD_START or event == Input.Dial.Events.HOLD_START:
            self.on_key_hold_start()
        elif event == Input.Dial.Events.TURN_CW:
            self.on_dial_turn(+1)
        elif event == Input.Dial.Events.TURN_CCW:
            self.on_dial_turn(-1)
        elif event == Input.Dial.Events.SHORT_UP:
            self.on_dial_down()

    def on_key_hold_start(self):
        self.load_settings()
        self.display_info()
        self.display_device_name()

    def on_dial_turn(self, direction: int):
        pass

    def on_dial_down(self):
        pass

    #
    # DISPLAY
    #

    def display_device_name(self):
        if not self.show_device_name:
            self.set_top_label("")
            return

        if self.device_nick:
            self.set_top_label(self.device_nick)
        elif self.use_standard:
            device = get_standard_device(self.device_filter)
            name = filter_proplist(device.proplist)
            self.set_top_label(name)
        else:
            self.set_top_label(self.device_name)

    def display_info(self):
        if self.info_content == InfoContent.VOLUME:
            info = self.display_volume()
        elif self.info_content == InfoContent.ADJUSTMENT:
            info = self.display_adjustment()
        else:
            info = ""

        if not self.show_info:
            info = ""

        self.set_bottom_label(info)

    def display_volume(self):
        if self.use_standard:
            device_name = get_standard_device(self.device_filter).name
            volumes = get_volumes_from_device(self.device_filter, device_name)
        else:
            volumes = get_volumes_from_device(self.device_filter, self.pulse_device_name)
        if len(volumes) > 0:
            return str(int(volumes[0]))
        return "N/A"

    def display_adjustment(self):
        return ""

    #
    # MISC
    #

    def set_device_settings(self):
        for device in get_device_list(self.device_filter):
            if device.description.__contains__("Monitor"):
                continue

            device_name = filter_proplist(device.proplist)

            if device_name == self.device_name:
                self.device_index = device.index
                self.pulse_device_name = device.name
                break

    def translate(self, key):
        return self.plugin_base.locale_manager.get(key)

    def create_asset_manager_window(self):
        self.asset_manager_window = Window(self.plugin_base.asset_manager)
        self.asset_manager_window.connect("close-request", self.manager_destroyed)

    def manager_destroyed(self, *args):
        self.asset_manager_window = None