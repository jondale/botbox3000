# coding=utf-8
#
# Copyright (C) 2024, Martin Owens
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
RGB Colors
"""

from ..color import ColorError
from .css import CssColor


class ColorRGB(CssColor):
    """
    Parse multiple versions of RGB from CSS module and standard hex formats.
    """

    name = "rgb"
    channels = ("red", "green", "blue")
    scales = ((0, 255), (0, 255), (0, 255), (0.0, 1.0))

    css_noalpha_prefix = "rgb"
    css_alpha_prefix = "rgba"

    red = property(lambda self: self[0], lambda self, value: self.__setitem__(0, value))
    green = property(
        lambda self: self[1], lambda self, value: self.__setitem__(1, value)
    )
    blue = property(
        lambda self: self[2], lambda self, value: self.__setitem__(2, value)
    )

    @classmethod
    def can_parse(cls, string: str) -> bool:
        return "icc" not in string and (
            string.startswith("#")
            or string.lstrip("-").isdigit()
            or super().can_parse(string)
        )

    def __init__(self, value, alpha=None):
        # Not CSS, but inkscape, some old color values stores as 32bit int strings
        if isinstance(value, str) and value.lstrip("-").isdigit():
            value = int(value)

        if isinstance(value, int):
            super().__init__(
                [
                    ((value >> 24) & 255),  # red
                    ((value >> 16) & 255),  # green
                    ((value >> 8) & 255),  # blue
                    ((value & 255) / 255.0),
                ]
            )  # opacity

        elif isinstance(value, str) and value.startswith("#") and " " not in value:
            if len(value) == 4:  # (css: #rgb -> #rrggbb)
                # pylint: disable=consider-using-f-string
                value = "#{1}{1}{2}{2}{3}{3}".format(*value)
            elif len(value) == 5:  # (css: #rgba -> #rrggbbaa)
                # pylint: disable=consider-using-f-string
                value = "#{1}{1}{2}{2}{3}{3}{4}{4}".format(*value)

            # Convert hex to integers
            try:
                values = [int(value[i : i + 2], 16) for i in range(1, len(value), 2)]
                if len(values) == 4:
                    values[3] /= 255
                super().__init__(values)
            except ValueError as error:
                raise ColorError(f"Bad RGB hex color value '{value}'") from error
        else:
            super().__init__(value, alpha=alpha)

    def __str__(self) -> str:
        if self.alpha is not None:
            return super().__str__()
        if len(self) < len(self.channels):
            raise ColorError(
                f"Incorrect number of channels for Color Space {self.name}"
            )
        # Always hex values when outputting color
        return "#{0:02x}{1:02x}{2:02x}".format(*(int(v) for v in self))  # pylint: disable=consider-using-f-string

    def __int__(self) -> int:
        return (
            (self[0] << 24)
            + (self[1] << 16)
            + (self[2] << 8)
            + int((self.alpha or 1.0) * 255)
        )
