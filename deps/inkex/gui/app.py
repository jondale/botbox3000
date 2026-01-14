# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2011-2022 Martin Owens <doctormo@geek-2.com>

"""
Wraps Gtk.Application, providing a way to load a Gtk.Builder
with a specific ui file containing windows, and building
a usable pythonic interface from them.
"""

import os
import logging

from gi.repository import Gtk, Gdk, Gio


class GtkApp(Gtk.Application):
    """A very thin wrapper around Gtk.Application"""

    app_name = None
    """The application id"""

    prefix = ""
    """Folder prefix added to ui_dir"""

    ui_dir = "./"
    """This is often the local directory"""

    ui_file = None
    """If a single file is used for multiple windows"""

    def __init__(self, **kwargs):
        """Creates a new GtkApp."""
        self.kwargs = kwargs
        super().__init__(
            application_id=self.app_name, flags=Gio.ApplicationFlags.NON_UNIQUE
        )
        self.connect("activate", lambda _: self.on_activate())
        if self.ui_dir:
            icontheme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
            icontheme.add_search_path(self.ui_dir)

    def run_wrapped(self):
        """Calls self.run() but catches keyboard interrupts"""
        try:
            self.run()
        except KeyboardInterrupt:  # pragma: no cover
            logging.info("User Interrupted")

    def on_activate(self):
        """Called when the application is activated"""
        raise NotImplementedError("Must override on_activate in subclass")

    def get_ui_file(self, window):
        """Load any given ui file from a standard location"""
        paths = [
            os.path.join(self.ui_dir, self.prefix, f"{window}.ui"),
            os.path.join(self.ui_dir, self.prefix, f"{self.ui_file}.ui"),
        ]
        for path in paths:
            if os.path.isfile(path):
                return path
        raise FileNotFoundError(f"Gtk ui file is missing: {paths}")
