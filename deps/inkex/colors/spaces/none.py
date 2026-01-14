# coding=utf-8
#
# Copyright (C) 2021 Jonathan Neuhauser
#               2020 Martin Owens
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
An empty color for 'none'
"""

from ..color import Color, AlphaNotAllowed


class ColorNone(Color, AlphaNotAllowed):
    """A special color for 'none' colors"""

    name = "none"

    # Override opacity since none can not have opacity
    default_alpha = 0.0

    def __init__(self, value=None):
        pass

    def __str__(self) -> str:
        return "none"

    @classmethod
    def can_parse(cls, string: str) -> bool:
        """Returns true if this is the word 'none'"""
        return string == "none"

    @staticmethod
    def convert_to_rgb(*_):
        """Converting to RGB means transparent black"""
        return [0, 0, 0, 0]

    @staticmethod
    def convert_from_rgb(*_):
        """Converting from RGB means throwing out all data"""
        return []
