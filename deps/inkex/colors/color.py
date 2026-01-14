# coding=utf-8
#
# Copyright (C) 2020 Martin Owens
#               2021 Jonathan Neuhauser
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
Basic color controls
"""

from typing import Dict, Optional, Tuple, Union

from .converters import Converters

Number = Union[int, float]


def round_by_type(kind, number):
    """Round a number to zero or five decimal places depending on it's type"""
    return kind(round(number, kind == float and 5 or 0))


class ColorError(KeyError):
    """Specific color parsing error"""


class ColorIdError(ColorError):
    """Special color error for gradient and color stop ids"""


class Color(list):
    """A parsed color object which could be in many color spaces, the default is sRGB

    Can be constructed from valid CSS color attributes, as well as
    tuple/list + color space. Percentage values are supported.
    """

    _spaces: Dict[str, type] = {}

    name: Optional[str] = None

    # A list of known channels
    channels: Tuple[str, ...] = ()

    # A list of scales for converting css color values to known qantities
    scales: Tuple[
        Union[Tuple[Number, Number, bool], Tuple[Number, Number]], ...
    ] = ()  # Min (int/float), Max (int/float), [wrap around (bool:False)]

    # If alpha is not specified, this is the default for most color types.
    default_alpha = 1.0

    def __init_subclass__(cls):
        if not cls.name:
            return  # It is a base class

        # Add space to a dictionary of available color spaces
        cls._spaces[cls.name] = cls

        Converters.add_space(cls)

    def __new__(cls, value=None, alpha=None, arg=None):
        if not cls.name:
            if value is None:
                return super().__new__(cls._spaces["none"])

            if isinstance(value, int):
                return super().__new__(cls._spaces["rgb"])

            if isinstance(value, str):
                # String from xml or css attributes
                for space in cls._spaces.values():
                    if space.can_parse(value.lower()):
                        return super().__new__(space, value)

            if isinstance(value, Color):
                return super().__new__(type(value), value)

            if isinstance(value, (list, tuple)):
                from ..deprecated.main import _deprecated

                _deprecated(
                    "Anonymous lists of numbers for colors no longer default to rgb"
                )
                return super().__new__(cls._spaces["rgb"], value)

        return super().__new__(cls, value, alpha=alpha, arg=arg)

    def __init__(self, values, alpha=None, arg=None):
        super().__init__()

        if not self.name:
            raise ColorError(f"Not a known color value: '{values}' {arg}")

        if not isinstance(values, (list, tuple)):
            raise ColorError(
                f"Colors must be constructed with a list of values: '{values}'"
            )

        if alpha is not None and not isinstance(alpha, float):
            raise ColorError("Color alpha property must be a float number")

        if alpha is None and self.channels and len(values) == len(self.channels) + 1:
            alpha = values.pop()

        if isinstance(values, Color):
            alpha = values.alpha

        if self.channels and len(values) != len(self.channels):
            raise ColorError(
                f"You must have {len(self.channels)} channels for a {self.name} color"
            )

        self[:] = values
        self.alpha = alpha

    def __hash__(self):
        """Allow colors to be hashable"""
        return tuple(self + [self.alpha, self.name]).__hash__()

    def __str__(self):
        raise NotImplementedError(
            f"Color space {self.name} can not be printed to a string."
        )

    def __int__(self):
        raise NotImplementedError(
            f"Color space {self.name} can not be converted to a number."
        )

    def __getitem__(self, index):
        """Get the color value"""
        space = self.name

        if (
            isinstance(index, slice)
            and index.start is not None
            and not isinstance(index.start, int)
        ):
            # We support the format `value = color["space_name":index]` here
            space = self._spaces[index.start]
            index = int(index.stop)

        # Allow regular slicing to fall through more freely than setitem
        if space == self.name:
            return super().__getitem__(index)

        if not isinstance(index, int):
            raise ColorError(f"Unknown color getter definition: '{index}'")

        return self.to(space)[
            index
        ]  # Note: this calls Color.__getitem__ function again

    def __setitem__(self, index, value):
        """Set the color value in place, limits setter to specific color space"""
        space = self.name

        if isinstance(index, slice):
            # Support the format color[:] = [list of numbers] here
            if index.start is None and index.stop is None:
                super().__setitem__(
                    index, (self.constrain(ind, val) for ind, val in enumerate(value))
                )
                return

            # We support the format `color["space_name":index] = value` here
            space = self._spaces[index.start]
            index = int(index.stop)

        if not isinstance(index, int):
            raise ColorError(f"Unknown color setter definition: '{index}'")

        # Setting a channel in the existing space
        if space == self.name:
            super().__setitem__(index, self.constrain(index, value))
        else:
            # Set channel is another space, convert back and forth
            values = self.to(space)
            values[index] = value  # Note: this calls Color.__setitem__ function again
            self[:] = values.to(self.name)

    def to(self, space):  # pylint: disable=invalid-name
        """Get this color but in a specific color space"""
        if space in self._spaces.values():
            space = space.name
        if space not in self._spaces:
            raise AttributeError(
                f"Unknown color space {space} when converting from {self.name}"
            )
        if not hasattr(type(self), f"to_{space}"):
            setattr(
                type(self),
                f"to_{space}",
                Converters.find_converter(type(self), self._spaces[space]),
            )
        return getattr(self, f"to_{space}")()

    def __getattr__(self, name):
        if name.startswith("to_") and name.count("_") == 1:
            return lambda: self.to(name.split("_")[-1])
        raise AttributeError(f"Can not find attribute {type(self).__name__}.{name}")

    @property
    def effective_alpha(self):
        """Get the alpha as set, or tell me what it would be by default"""
        if self.alpha is None:
            return self.default_alpha
        return self.alpha

    def get_values(self, alpha=True):
        """Returns all values, including alpha as a list"""
        if alpha:
            return list(self + [self.effective_alpha])
        return list(self)

    @classmethod
    def to_units(cls, *values):
        """Convert the color values into floats scales from 0.0 to 1.0"""
        return [cls.scale_down(ind, val) for ind, val in enumerate(values)]

    @classmethod
    def from_units(cls, *values):
        """Convert float values to the scales expected and return a new instance"""
        return [cls.scale_up(ind, val) for ind, val in enumerate(values)]

    @classmethod
    def can_parse(cls, string):  # pylint: disable=unused-argument
        """Returns true if this string can be parsed for this color type"""
        return False

    @classmethod
    def scale_up(cls, index, value):
        """Convert from float 0.0 to 1.0 to an int used in css"""
        (min_value, max_value) = cls.scales[index][:2]
        return cls.constrain(
            index, (value * (max_value - min_value)) + min_value
        )  # See inkscape/src/colors/spaces/base.h:SCALE_UP

    @classmethod
    def scale_down(cls, index, value):
        """Convert from int, often 0 to 255 to a float 0.0 to 1.0"""
        (min_value, max_value) = cls.scales[index][:2]
        return (cls.constrain(index, value) - min_value) / (
            max_value - min_value
        )  # See inkscape/src/colors/spaces/base.h:SCALE_DOWN

    @classmethod
    def constrain(cls, index, value):
        """Constrains the value to the css scale"""
        scale = cls.scales[index]
        if len(scale) == 3 and scale[2] is True:
            if value == scale[1]:
                return value
            return round_by_type(
                type(scale[0]), value % scale[1]
            )  # Wrap around value (i.e. hue)
        return min(max(round_by_type(type(scale[0]), value), scale[0]), scale[1])

    def interpolate(self, other, fraction):
        """Interpolate two colours by the given fraction

        .. versionadded:: 1.1"""
        from ..tween import ColorInterpolator  # pylint: disable=import-outside-toplevel

        try:
            other = other.to(type(self))
        except ColorError:
            raise ColorError("Can not convert color in interpolation.")
        return ColorInterpolator(self, other).interpolate(fraction)


class AlphaNotAllowed:
    """Mixin class to indicate that alpha values are not permitted on this color space"""

    alpha = property(
        lambda self: None,
        lambda self, value: None,
    )

    def get_values(self, alpha=False):
        return super().get_values(False)
