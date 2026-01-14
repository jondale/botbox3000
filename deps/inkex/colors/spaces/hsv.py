# coding=utf-8
#
# Copyright (C) 2024 Jonathan Neuhauser
#               2024 Martin Owens
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
# pylint: disable=W0223
"""
HSV Color Space
"""

from .css import CssColorModule4


class ColorHSV(CssColorModule4):
    """
    Parse the HWB CSS Color Module 4 format and retain as HSV values.
    """

    name = "hsv"
    channels = ("hue", "saturation", "value")
    scales = ((0, 360, True), (0, 100), (0, 100), (0.0, 1.0))

    # We use HWB to store HSV as this makes the most sense to Inkscape
    css_either_prefix = "hwb"

    hue = property(lambda self: self[0], lambda self, value: self.__setitem__(0, value))
    saturation = property(
        lambda self: self[1], lambda self, value: self.__setitem__(1, value)
    )
    value = property(
        lambda self: self[2], lambda self, value: self.__setitem__(2, value)
    )

    @classmethod
    def parse_css_color(cls, value):
        """Parsing HWB as if it was HSV for css input"""
        prefix, values = super().parse_css_color(value)
        # See https://en.wikipedia.org/wiki/HWB_color_model#Converting_to_and_from_HSV
        values[1] /= 100
        values[2] /= 100
        scale = values[1] + values[2]
        if scale > 1.0:
            values[1] /= scale
            values[2] /= scale
        values[1] = int(
            (values[2] == 1.0 and 0.0 or (1.0 - (values[1] / (1.0 - values[2])))) * 100
        )
        values[2] = int((1.0 - values[2]) * 100)
        return prefix, values

    def get_css_values(self):
        """Convert our HSV values into HWB for css output"""
        values = list(self)
        values[1] = (100 - values[1]) * (values[2] / 100)
        values[2] = 100 - values[2]
        return values

    @staticmethod
    def convert_to_hsl(hue, saturation, value, *alpha):
        """Conversion according to
        https://en.wikipedia.org/wiki/HSL_and_HSV#HSV_to_HSL

        .. versionadded:: 1.5"""
        lum = value * (1 - saturation / 2)
        sat = 0 if lum in (0, 1) else (value - lum) / min(lum, 1 - lum)
        return [hue, sat, lum] + list(alpha)

    @staticmethod
    def convert_from_hsl(hue, saturation, lightness, *alpha):
        """Convertion according to Inkscape C++ codebase
        .. versionadded:: 1.5"""
        val = lightness + saturation * min(lightness, 1 - lightness)
        sat = 0 if val == 0 else 2 * (1 - lightness / val)
        return [hue, sat, val] + list(alpha)
