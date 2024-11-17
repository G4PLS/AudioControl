"""
Author: G4PLS
Year: 2024
"""

import gi

from GtkHelper.GtkHelper import better_disconnect

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw
from .AssetManager import AssetManager

class AssetPreview(Gtk.FlowBoxChild):
    def __init__(self, window: "AssetManagerWindow", name: str, size: tuple[int, int] = (50,50), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_css_classes(["asset-preview"])
        self.set_margin_start(5)
        self.set_margin_end(5)
        self.set_margin_top(5)
        self.set_margin_bottom(5)

        self.name = name
        self.size = size

        self.set_size_request(self.size[0], self.size[1])
        self.create_base_ui()

        self.reset_button.connect("clicked", window.reset_button_clicked, self)

    def create_base_ui(self):
        self.overlay = Gtk.Overlay()

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.set_size_request(self.size[0], self.size[1])

        self.overlay.set_child(self.main_box)

        self.reset_button = Gtk.Button(icon_name="edit-undo-symbolic")
        self.reset_button.set_halign(Gtk.Align.END)
        self.reset_button.set_valign(Gtk.Align.START)
        self.reset_button.set_margin_top(10)
        self.reset_button.set_margin_end(10)
        self.overlay.add_overlay(self.reset_button)

        self.set_child(self.overlay)

        self.set_size_request(self.size[0], self.size[1])

    def build(self):
        pass

class AssetManagerWindow(Adw.PreferencesWindow):
    def __init__(self, asset_manager: AssetManager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.asset_manager = asset_manager

        self.set_default_size(500, 500)

    def build_asset_page(self, title, group_name, icon_name):
        page = Adw.PreferencesPage(title=title)
        group = Adw.PreferencesGroup(title=group_name)
        page.add(group)
        page.set_icon_name(icon_name)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        group.add(main_box)

        search_entry = Gtk.SearchEntry()
        search_entry.set_placeholder_text("Search Asset...")
        main_box.append(search_entry)

        scrolled_window = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        group.add(scrolled_window)

        flow_box = Gtk.FlowBox(hexpand=True, orientation=Gtk.Orientation.HORIZONTAL,
                                    selection_mode=Gtk.SelectionMode.SINGLE, valign=Gtk.Align.START)
        flow_box.set_max_children_per_line(3)
        flow_box.set_row_spacing(5)
        flow_box.set_column_spacing(5)

        scrolled_window.set_child(flow_box)

        return page, flow_box

    def connect_flow_box(self, flow_box: Gtk.FlowBox, callback: callable):
        flow_box.connect("child-activated", callback)

    def disconnect_flow_box(self, flow_box: Gtk.FlowBox, callback: callable):
        better_disconnect(flow_box, callback)

    def reset_button_clicked(self, *args):
        pass