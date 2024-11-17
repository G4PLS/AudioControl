"""
Author: G4PLS
Year: 2024
"""
from src.backend.DeckManagement.ImageHelpers import image2pixbuf
from .AssetDisplays import AssetManagerWindow, AssetPreview
from .AssetManager import AssetManager, Icon, Color

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Gio, GdkPixbuf, Pango, Gdk

class IconPreview(AssetPreview):
    def __init__(self, image, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.image = image
        self.pixbuf = image2pixbuf(image)
        self.build()

    def scale_pixbuf(self):
        original_width = self.pixbuf.get_width()
        original_height = self.pixbuf.get_height()
        w = self.size[0]
        h = self.size[1]

        scale = min(w / original_width, h / original_height)

        new_width = int(original_width * scale)
        new_height = int(original_height * scale)

        return self.pixbuf.scale_simple(new_width, new_height, GdkPixbuf.InterpType.BILINEAR)

    def build(self):
        self.picture = Gtk.Picture(width_request=self.size[0], height_request=self.size[1], overflow=Gtk.Overflow.HIDDEN,
                                   content_fit=Gtk.ContentFit.COVER,
                                   hexpand=False, vexpand=False, keep_aspect_ratio=True)
        self.picture.set_pixbuf(self.scale_pixbuf())

        self.main_box.append(self.picture)

        self.label = Gtk.Label(label=self.name, xalign=Gtk.Align.CENTER, hexpand=False, ellipsize=Pango.EllipsizeMode.END,
                               max_width_chars=20,
                               margin_start=20, margin_end=20)
        self.main_box.append(self.label)

    def set_image(self, image):
        self.image = image
        self.pixbuf = image2pixbuf(self.image)
        self.picture.set_pixbuf(self.scale_pixbuf())

class ColorPreview(AssetPreview):
    def __init__(self, color: tuple[int, int, int, int], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.color = color
        self.build()

    def build(self):
        self.color_button = Gtk.ColorButton(title="Pick Color")
        self.color_button.set_sensitive(False)
        self.set_color(self.color)
        self.color_button.set_size_request(self.size[0], self.size[1])

        self.main_box.append(self.color_button)

        self.label = Gtk.Label(label=self.name, xalign=Gtk.Align.CENTER, hexpand=False, ellipsize=Pango.EllipsizeMode.END,
                               max_width_chars=20,
                               margin_start=20, margin_end=20)
        self.main_box.append(self.label)

    def set_color(self, color: tuple[int, int, int, int]):
        self.color = color
        self.color_button.set_rgba(self.get_rgba())

    def set_color_rgba(self, color: Gdk.RGBA):
        normalized = (color.red * 255,
                      color.green * 255,
                      color.blue * 255,
                      color.alpha * 255)
        self.color = normalized
        self.color_button.set_rgba(color)

    def get_rgba(self):
        rgba = Gdk.RGBA()
        normalized = tuple(color / 255.0 for color in self.color)
        rgba.red = normalized[0]
        rgba.green = normalized[1]
        rgba.blue = normalized[2]
        rgba.alpha = normalized[3]
        return rgba

class Window(AssetManagerWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        icon_page, icon_box = self.build_asset_page("Icons", "Select Icons", "image-x-generic-symbolic")
        color_page, color_box = self.build_asset_page("Colors", "Select Colors", "color-select-symbolic")

        icon_page.set_icon_name()

        self.add(icon_page)
        self.add(color_page)

        self.connect_flow_box(icon_box, self.on_icon_clicked)
        self.connect_flow_box(color_box, self.on_color_clicked)

        self.display_icons(icon_box)
        self.display_colors(color_box)

    #
    # EVENTS
    #

    # Icon

    def on_icon_clicked(self, flow_box, preview: IconPreview):
        icon_dialog = Gtk.FileDialog.new()
        icon_dialog.set_title("Icon")

        icon_dialog.open(self, None, self.on_icon_dialog_response, preview)

    def on_icon_dialog_response(self, dialog: Gtk.FileDialog, task, preview: IconPreview):
        file = dialog.open_finish(task)

        if file:
            file_path = file.get_path()
            self.asset_manager.icons.add_override(preview.name, Icon(path=file_path), override=True)

            _, render = self.asset_manager.icons.get_asset_values(preview.name)
            preview.set_image(render)
            self.asset_manager.save()

    # Color

    def on_color_clicked(self, flow_box, preview: ColorPreview):
        color_dialog = Gtk.ColorDialog.new()
        color_dialog.set_title("Color")

        # Open the dialog
        color_dialog.choose_rgba(self, preview.get_rgba(), None, self.on_color_dialog_response, preview)

    def on_color_dialog_response(self, dialog: Gtk.ColorDialog, task: Gio.Task, preview: ColorPreview):
        rgba = dialog.choose_rgba_finish(task)
        preview.set_color_rgba(rgba)
        self.asset_manager.colors.add_override(preview.name, Color(color=preview.color), override=True)
        self.asset_manager.save()

    #
    # DISPLAY
    #

    def display_icons(self, flow_box):
        icons = self.asset_manager.icons.get_assets_merged()

        for name, icon in icons.items():
            _, render = icon.get_values()

            preview = IconPreview(window=self, name=name, image=render, size=(100, 100), vexpand=False, hexpand=False)
            flow_box.append(preview)

    def display_colors(self, flow_box):
        colors = self.asset_manager.colors.get_assets_merged()

        for name, color in colors.items():
            color = color.get_values()
            preview = ColorPreview(window=self, name=name, color=color, size=(100, 100), hexpand=False, vexpand=False)
            flow_box.append(preview)

    def reset_button_clicked(self, *args):
        preview = args[1]
        if type(preview) == IconPreview:
            self.asset_manager.icons.remove_override(preview.name)
            _, render = self.asset_manager.icons.get_asset(preview.name).get_values()
            preview.set_image(render)
            self.asset_manager.save()
        elif type(preview) == ColorPreview:
            self.asset_manager.colors.remove_override(preview.name)
            preview.set_color(self.asset_manager.colors.get_asset(preview.name).get_values())
            self.asset_manager.save()