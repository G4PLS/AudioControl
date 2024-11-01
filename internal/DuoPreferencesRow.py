"""
Author: G4PLS
Year: 2024

This adds a simple new UI element which takes two Gtk.Widgets and adds them side by side
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

class DuoPreferencesRow(Adw.PreferencesRow):
    def __init__(self, primary_widget: Gtk.Widget = None, secondary_widget: Gtk.Widget = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                                margin_start=10, margin_end=10,
                                margin_top=10, margin_bottom=10)

        self.primary_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True)
        self.secondary_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True)

        self.set_child(self.main_box)

        self.main_box.append(self.primary_box)
        self.main_box.append(self.secondary_box)

        self.set_primary_widget(primary_widget)
        self.set_secondary_widget(secondary_widget)

    def set_primary_widget(self, widget: Gtk.Widget):
        self.primary_widget = widget

        self.main_box.remove(self.primary_box) # Removes Widget Box
        self.primary_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True) # Re-Creates Widget Box
        self.main_box.prepend(self.primary_box)  # Re-Add Widget Box

        if self.primary_widget:
            self.primary_box.append(self.primary_widget) # Adds widget to Box


    def set_secondary_widget(self, widget: Gtk.Widget):
        self.secondary_widget = widget

        self.main_box.remove(self.secondary_box) # Removes Widget Box
        self.secondary_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True) # Re-Creates Widget Box
        self.main_box.append(self.secondary_box) # Re-Add Widget Box

        if self.secondary_widget:
            self.secondary_box.append(self.secondary_widget)  # Adds widget to Box