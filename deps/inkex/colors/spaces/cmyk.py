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
DeviceCMYK Color Space
"""

from .css import CssColorModule4


class ColorDeviceCMYK(CssColorModule4):
    """
    Parse the device-cmyk CSS Color Module 4 format.

    Note that this format is NOT true CMYK as you might expect in a printer and
    is instead is an aproximation of the intended ink levels if this was converted
    into a real CMYK color profile using a color management system.
    """

    name = "cmyk"

    channels = ("cyan", "magenta", "yellow", "black")
    scales = ((0, 100), (0, 100), (0, 100), (0, 100), (0.0, 1.0))
    css_either_prefix = "device-cmyk"

    cyan = property(
        lambda self: self[0], lambda self, value: self.__setitem__(0, value)
    )
    magenta = property(
        lambda self: self[1], lambda self, value: self.__setitem__(1, value)
    )
    yellow = property(
        lambda self: self[2], lambda self, value: self.__setitem__(2, value)
    )
    black = property(
        lambda self: self[3], lambda self, value: self.__setitem__(3, value)
    )

    @staticmethod
    def convert_to_rgb(cyan, magenta, yellow, black, *alpha):
        """
        Convert a set of Device-CMYK identities into RGB
        """
        white = 1.0 - black
        return [
            1.0 - min((1.0, cyan * white + black)),
            1.0 - min((1.0, magenta * white + black)),
            1.0 - min((1.0, yellow * white + black)),
        ] + list(alpha)

    @staticmethod
    def convert_from_rgb(red, green, blue, *alpha):
        """
        Convert RGB into Device-CMYK
        """
        white = max((red, green, blue))
        black = 1.0 - white
        return [
            # Each channel is it's color chart oposite (cyan->red)
            # with a bit of white removed.
            (white and (1.0 - red - black) / white or 0.0),
            (white and (1.0 - green - black) / white or 0.0),
            (white and (1.0 - blue - black) / white or 0.0),
            black,
        ] + list(alpha)
