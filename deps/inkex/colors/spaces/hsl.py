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
# pylint: disable=W0223
"""
HSL Color Space
"""

from .css import CssColor


class ColorHSL(CssColor):
    """
    Parse the HSL CSS Module Module 3 format.
    """

    name = "hsl"
    channels = ("hue", "saturation", "lightness")
    scales = ((0, 360, True), (0, 100), (0, 100), (0.0, 1.0))

    css_noalpha_prefix = "hsl"
    css_alpha_prefix = "hsla"

    hue = property(lambda self: self[0], lambda self, value: self.__setitem__(0, value))
    saturation = property(
        lambda self: self[1], lambda self, value: self.__setitem__(1, value)
    )
    lightness = property(
        lambda self: self[2], lambda self, value: self.__setitem__(2, value)
    )

    @staticmethod
    def convert_from_rgb(red, green, blue, alpha=None):
        """RGB to HSL colour conversion"""
        rgb_max = max(red, green, blue)
        rgb_min = min(red, green, blue)
        delta = rgb_max - rgb_min
        hsl = [0.0, 0.0, (rgb_max + rgb_min) / 2.0]

        if delta != 0:
            if hsl[2] <= 0.5:
                hsl[1] = delta / (rgb_max + rgb_min)
            else:
                hsl[1] = delta / (2 - rgb_max - rgb_min)

            if red == rgb_max:
                hsl[0] = (green - blue) / delta
            elif green == rgb_max:
                hsl[0] = 2.0 + (blue - red) / delta
            elif blue == rgb_max:
                hsl[0] = 4.0 + (red - green) / delta

            hsl[0] /= 6.0
            if hsl[0] < 0:
                hsl[0] += 1
            if hsl[0] > 1:
                hsl[0] -= 1
        if alpha is not None:
            hsl.append(alpha)
        return hsl

    @staticmethod
    def convert_to_rgb(hue, sat, light, *alpha):
        """HSL to RGB Color Conversion"""
        if sat == 0:
            return [light, light, light]  # Gray

        if light < 0.5:
            val2 = light * (1 + sat)
        else:
            val2 = light + sat - light * sat
        val1 = 2 * light - val2
        ret = [
            _hue_to_rgb(val1, val2, hue * 6 + 2.0),
            _hue_to_rgb(val1, val2, hue * 6),
            _hue_to_rgb(val1, val2, hue * 6 - 2.0),
        ]
        return ret + list(alpha)


def _hue_to_rgb(val1, val2, hue):
    if hue < 0:
        hue += 6.0
    if hue > 6:
        hue -= 6.0
    if hue < 1:
        return val1 + (val2 - val1) * hue
    if hue < 3:
        return val2
    if hue < 4:
        return val1 + (val2 - val1) * (4 - hue)
    return val1
