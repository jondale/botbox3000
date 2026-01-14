# coding=utf-8
#
# Copyright (C) 2018-2024 Martin Owens
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
Parsing CSS elements from colors
"""

from typing import Optional, Union

from ..color import Color, ColorError, ColorIdError


class CssColor(Color):
    """
    A Color which is always parsed and printed from a css format.
    """

    # A list of css prefixes which ar valid for this space
    css_noalpha_prefix: Optional[str] = None
    css_alpha_prefix: Optional[str] = None
    css_either_prefix: Optional[str] = None

    # Some CSS formats require commas, others do not
    css_join: str = ", "
    css_join_alpha: str = ", "
    css_func = "color"

    def __str__(self):
        values = self.css_join.join([f"{v:g}" for v in self.get_css_values()])
        prefix = self.css_noalpha_prefix or self.css_either_prefix
        if self.alpha is not None:
            # Alpha is stored as a percent for clarity
            alpha = int(self.alpha * 100)
            values += self.css_join_alpha + f"{alpha}%"
            if not self.css_either_prefix:
                prefix = self.css_alpha_prefix
        if prefix is None:
            raise ColorError(f"Can't encode color {self.name} into CSS color format.")
        return f"{prefix}({values})"

    @classmethod
    def can_parse(cls, string: str):
        string = string.replace(" ", "")
        if "(" not in string or ")" not in string:
            return False
        for prefix in (
            cls.css_noalpha_prefix,
            cls.css_alpha_prefix,
            cls.css_either_prefix,
        ):
            if prefix and (prefix + "(" in string or "color(" + prefix in string):
                return True
        return False

    def __init__(self, value, alpha=None):
        if isinstance(value, str):
            prefix, values = self.parse_css_color(value)
            has_alpha = (
                self.channels is not None and len(values) == len(self.channels) + 1
            )

            if prefix == self.css_noalpha_prefix or (
                prefix == self.css_either_prefix and not has_alpha
            ):
                super().__init__(values)

            elif prefix == self.css_alpha_prefix or (
                prefix == self.css_either_prefix and has_alpha
            ):
                super().__init__(values, values.pop())
            else:
                raise ColorError(f"Could not parse {self.name} css color: '{value}'")
        else:
            super().__init__(value, alpha=alpha)

    @classmethod
    def parse_css_color(cls, value):
        """Parse a css string into a list of values and it's color space prefix"""
        prefix, values = value.lower().strip().strip(")").split("(")
        # Some css formats use commas, others do not
        if "," in cls.css_join:
            values = values.replace(",", " ")
        if "/" in cls.css_join_alpha:
            values = values.replace("/", " ")

        # Split values by spaces
        values = values.split()
        prefix = prefix.strip()
        if prefix == cls.css_func:
            prefix = values.pop(0)
        if prefix == "url":
            raise ColorIdError("Can not parse url as if it was a color.")
        return prefix, [cls.parse_css_value(i, v) for i, v in enumerate(values)]

    def get_css_values(self):
        """Return a list of values used for css string output"""
        return self

    @classmethod
    def parse_css_value(cls, index, value) -> Union[int, float]:
        """Parse a CSS value such as 100%, 360 or 0.4"""
        if cls.scales and index >= len(cls.scales):
            raise ValueError("Can't add any more values to color.")

        if isinstance(value, str):
            value = value.strip()
            if value.endswith("%"):
                value = float(value.strip("%")) / 100
            elif "." in value:
                value = float(value)
            else:
                value = int(value)

        if isinstance(value, float) and value <= 1.0:
            value = cls.scale_up(index, value)
        return cls.constrain(index, value)


class CssColorModule4(CssColor):
    """Tweak the css parser for CSS Module Four formating"""

    css_join = " "
    css_join_alpha = " / "
