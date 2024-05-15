import enum

from GtkHelper.GtkHelper import ComboRow
from src.backend.PluginManager.ActionBase import ActionBase

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw


class PulseFilter(enum.StrEnum):
    SINK = "sink",
    SOURCE = "source",


class DeviceBase(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Mostly used for Displaying
        self.device_display_name: str = None
        self.info: str = None

        # Internal use for Events and faster lookups
        self.pulse_device_name: str = None
        self.device_index: int = None

        # Used for Filtering devices
        self.pulse_filter: PulseFilter = PulseFilter.SINK

        # Used for Display on the Streamdeck
        self.show_device_name: bool = False
        self.show_info: bool = False

        # Every Action will have a Configuration so this works out fine
        self.has_configuration = True

    def on_ready(self):
        self.load_essential_settings()

    def get_config_rows(self):
        self.device_filter_model = Gtk.ListStore.new([str, str])
        self.device_model = Gtk.ListStore.new([str])

        # Create ComboRow
        self.device_filter_row = ComboRow(title=self.plugin_base.lm.get("DEVICE FILTER"),
                                          model=self.device_filter_model)
        self.device_row = ComboRow(title=self.plugin_base.lm.get("DEVICE"),
                                   model=self.device_model)

        # Set Combo Row Renderers
        self.device_cell_renderer = Gtk.CellRendererText()
        self.device_row.combo_box.pack_start(self.device_cell_renderer, True)
        self.device_row.combo_box.add_attribute(self.device_cell_renderer, "text", 0)

        self.device_filter_cell_renderer = Gtk.CellRendererText()
        self.device_filter_row.combo_box.pack_start(self.device_cell_renderer, True)
        self.device_filter_row.combo_box.add_attribute(self.device_cell_renderer, "text", 0)

        # Basic Settings
        self.show_device_switch = Adw.SwitchRow(title="SHOW DEVICE NAME")
        self.show_info_switch = Adw.SwitchRow(title="SHOW INFO")

        # Load Models
        self.load_filter_model()
        self.load_device_model()

        # Load Settings
        self.load_ui_settings()

        # Connect Events
        self.connect_events()

        return [self.device_filter_row, self.device_row, self.show_device_switch, self.show_info_switch]

    #
    # BASE MODEL LOADER
    #

    def load_filter_model(self):
        self.device_filter_model.clear()

        switch = {
            PulseFilter.SINK: ["Output Device", PulseFilter.SINK],
            PulseFilter.SOURCE: ["Input Device", PulseFilter.SOURCE]
        }

        for filter in PulseFilter:
            text = switch.get(filter, [])

            if text:
                self.device_filter_model.append(text)

    def load_device_model(self):
        self.device_model.clear()

        for device in self.get_device_list(self.pulse_filter):
            if device.description.__contains__("Monitor"):
                continue

            device_name = self.filter_proplist(device.proplist)

            if device_name is not None:
                self.device_model.append([device_name])

    #
    # BASE SETTINGS LOADER
    #

    def load_essential_settings(self):
        settings = self.get_settings()

        self.pulse_device_name = settings.get("pulse-name", None)
        self.pulse_filter = PulseFilter(settings.get("device-filter", PulseFilter.SINK))
        self.show_device_name = settings.get("show-device-name", False)
        self.show_info = settings.get("show-info", False)

        if self.pulse_device_name:
            device = self.get_device(self.pulse_filter)

            if not device:
                return

            self.device_index = device.index
            self.device_display_name = self.filter_proplist(device.proplist)

        self.display_device_name()
        self.display_info()

    def load_ui_settings(self):
        for i, filter in enumerate(self.device_filter_model):
            if filter[1] == self.pulse_filter:
                self.device_filter_row.combo_box.set_active(i)
                break
        else:
            self.device_filter_row.combo_box.set_active(-1)

        for i, device in enumerate(self.device_model):
            if device[0] == self.device_display_name:
                self.device_row.combo_box.set_active(i)
                break
        else:
            self.device_row.combo_box.set_active(-1)

        self.show_device_switch.set_active(self.show_device_name)
        self.show_info_switch.set_active(self.show_info)

    #
    # EVENTS
    #

    def connect_events(self):
        self.device_filter_row.combo_box.connect("changed", self.on_device_filter_changed)
        self.device_row.combo_box.connect("changed", self.on_device_changed)
        self.show_device_switch.connect("notify::active", self.on_show_device_changed)
        self.show_info_switch.connect("notify::active", self.on_show_info_changed)

    def disconnect_events(self):
        self.device_filter_row.combo_box.disconnect_by_func(self.on_device_filter_changed)
        self.device_row.combo_box.disconnect_by_func(self.on_device_changed)
        self.show_device_switch.disconnect_by_func(self.on_show_device_changed)
        self.show_info_switch.disconnect_by_func(self.on_show_info_changed)

    def on_device_filter_changed(self, *args, **kwargs):
        settings = self.get_settings()

        self.pulse_filter = self.device_filter_model[self.device_filter_row.combo_box.get_active()][1]
        self.device_display_name = None
        self.info = None

        self.disconnect_events()
        self.load_device_model()
        self.connect_events()

        self.display_device_name()
        self.display_info()

        settings["device-filter"] = self.pulse_filter
        settings["pulse-name"] = self.device_display_name
        self.set_settings(settings)

    def on_device_changed(self, *args, **kwargs):
        settings = self.get_settings()

        self.device_display_name = self.device_model[self.device_row.combo_box.get_active()][0]

        for device in self.get_device_list(self.pulse_filter):
            if device.description.__contains__("Monitor"):
                continue

            device_name = self.filter_proplist(device.proplist)

            if device_name == self.device_display_name:
                self.device_index = device.index
                self.pulse_device_name = device.name
                break

        self.display_device_name()
        self.display_info()

        settings["pulse-name"] = self.pulse_device_name
        self.set_settings(settings)

    def on_show_device_changed(self, *args, **kwargs):
        settings = self.get_settings()

        self.show_device_name = self.show_device_switch.get_active()
        self.display_device_name()

        settings["show-device-name"] = self.show_device_name
        self.set_settings(settings)

    def on_show_info_changed(self, *args, **kwargs):
        settings = self.get_settings()

        self.show_info = self.show_info_switch.get_active()
        self.display_info()

        settings["show-info"] = self.show_info
        self.set_settings(settings)

    #
    # MISC
    #

    def filter_proplist(self, proplist) -> [str, None]:
        if not proplist.get("alsa.card"):
            node_name = proplist.get("node.name")
            if not node_name:
                node_name = self.filter_alsa(proplist)
            return node_name

        # Now we know its alsa
        device_name = self.filter_alsa(proplist)

        return device_name

    def filter_alsa(self, proplist):
        return (proplist.get("device.product.name") or proplist.get("device.nick") or
                proplist.get("device.description") or None)

    def get_device(self, filter: PulseFilter):
        try:
            if filter == PulseFilter.SINK:
                return self.plugin_base.pulse.get_sink_by_name(self.pulse_device_name)
            elif filter == PulseFilter.SOURCE:
                return self.plugin_base.pulse.get_source_by_name(self.pulse_device_name)
        except:
            self.show_error(1)
        return None

    def get_device_list(self, filter: PulseFilter):
        switch = {
            PulseFilter.SINK: self.plugin_base.pulse.sink_list(),
            PulseFilter.SOURCE: self.plugin_base.pulse.source_list(),
        }

        return switch.get(filter, {})

    #
    # DISPLAY
    #

    def display_device_name(self):
        if self.show_device_name:
            self.set_top_label(self.device_display_name)
        else:
            self.set_top_label("")

    def display_info(self):
        if self.show_info:
            self.set_bottom_label(self.info)
        else:
            self.set_bottom_label("")

    #
    # MISC
    #

    def get_volumes_from_device(self):
        try:
            device = self.get_device(self.pulse_filter)
            device_volumes = device.volume.values
            return [round(vol*100) for vol in device_volumes]
        except:
            return []