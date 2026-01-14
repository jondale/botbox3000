# coding=utf-8
#
# Copyright (C) 2024 Martin Owens
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
"""
SVG icc-color parser
"""

from ..color import Color, AlphaNotAllowed, ColorError, round_by_type
from .css import CssColor
from .rgb import ColorRGB


class ColorCMS(CssColor, AlphaNotAllowed):
    """
    Parse and print SVG icc-color objects into their values and the fallback RGB
    """

    name = "cms"
    css_func = "icc-color"
    channels = ()
    scales = ()

    def __init__(self, values, icc_profile=None, fallback=None):
        if isinstance(values, str):
            if values.strip().startswith("#") and " " in values:
                fallback, values = values.split(" ", 1)
                fallback = Color(fallback)
            icc_profile, values = self.parse_css_color(values)

        if icc_profile is None:
            raise ColorError("CMS Color requires an icc color profile name.")

        self.icc_profile = icc_profile
        self.fallback_rgb = fallback
        super().__init__(values)

    def __str__(self) -> str:
        values = self.css_join.join([f"{v:g}" for v in self.get_css_values()])
        fallback = str(ColorRGB(self.fallback_rgb)) + " " if self.fallback_rgb else ""
        return f"{fallback}{self.css_func}({self.icc_profile}, {values})"

    @classmethod
    def can_parse(cls, string: str) -> bool:
        # Custom detection because of RGB fallback prefix
        return "icc-color" in string.replace("(", " ").split()

    @classmethod
    def constrain(cls, index, value):
        return min(max(round_by_type(float, value), 0.0), 1.0)

    @classmethod
    def scale_up(cls, index, value):
        return value  # All cms values are already 0.0 to 1.0

    @classmethod
    def scale_down(cls, index, value):
        return value  # All cms values are already 0.0 to 1.0

    @staticmethod
    def convert_to_rgb(*data):
        """Catch attempted conversions to rgb"""
        raise NotImplementedError("Can not convert to RGB from icc color")

    @staticmethod
    def convert_from_rgb(*data):
        """Catch attempted conversions from rgb"""
        raise NotImplementedError("Can not convert from RGB to icc color")


# This is research code for a future developer to use. We already use PIL and this will
# allow icc colors to be converted in python. This isn't needed right now, so this work
# will be left undone.
#    @staticmethod
#    def convert_to_rgb():
#        from PIL import Image, ImageCms
#        pixel = Image.fromarray([[int(r * 255), int(g * 255), int(b * 255)]], 'RGB')
#        transform = ImageCms.buildTransform(sRGB_profile, self.this_profile, "RGB",
#                        self.this_profile_mode, self.this_rendering_intent, 0)
#        transform.apply_in_place(pixel)
#        return [p / 255 for p in pixel[0]]
