# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2012-2022 Martin Owens <doctormo@geek-2.com>

"""
Wraps Gtk.Window with something a little nicer.
"""

from gi.repository import Gtk


class Window:
    """A very thin wrapper around Gtk.Window"""

    name = None
    """The name of the window to load from the ui file"""

    def __init__(self, gapp):
        """Create a new Window and load its Gtk.Window from a ui file"""
        self.gapp = gapp
        ui_file = gapp.get_ui_file(self.name)

        # Set up the builder and load ui
        self.builder = Gtk.Builder(self)
        self.builder.set_translation_domain(gapp.app_name)
        self.builder.add_from_file(ui_file)
        self.widget = self.builder.get_object

        # Find the window in the ui
        self.window = self.widget(self.name)
        if not self.window:  # pragma: no cover
            raise KeyError(f"Missing window widget '{self.name}' from '{ui_file}'")

        # Keep application alive
        self.window.set_application(self.gapp)

    def close(self, widget=None):
        """Closes the window. Can be connected to signals."""
        self.window.close()
