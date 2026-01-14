# coding=utf-8
"""
The color module allows for the parsing and printing of CSS colors in an SVG document.

Support formats are currently:

    1. #RGB #RRGGBB #RGBA #RRGGBBAA formats
    2. Named colors such as 'red'
    3. icc-color(...) which is specific to SVG 1.1
    4. rgb(...) and rgba(...) from CSS Color Module 3
    5. hsl(...) and hsla(...) from CSS Color Module 3
    6. hwb(...) from CSS Color Module 4, but encoded internally as hsv
    7. device-cmyk(...) from CSS Color Module 4

Each color space has it's own class, such as ColorRGB. Each space will parse multiple
formats, for example ColorRGB supports hex and rgb CSS module formats.

Each color object is a list of numbers, each number is a channel in that color space
with alpha channel being held in it's own property which may be a unit number or None.

The numbers a color stores are typically in the range defined in the CSS module
specification so for example RGB, all the numbers are between 0-255 while for hsl
the hue channel is between 0-360 and the saturation and lightness are between 0-100.

To get normalised numbers you can use to the `to_units` function to get everything 0-1

Each Color space type has a name value which can be used to identify the color space,
if this is more useful than checking the class type. Either can be used when converting
the color values between spaces.

A color object may be converted into a different space by using the
`color.to(other_space)` function, which will return a new color object in the requested
space.

There are three special cases.

 1. ColorNamed is a type of ColorRGB which will preferentially print the name instead
    of the hex value if one is available.
 2. ColorNone is a special value which indicates the keyword `none` and does not
    allow any values or alpha.
 3. ColorCMS can not be converted to other color spaces and contains a `fallback_color`
    to access the RGB fallback if it was provided.

"""

from .color import Color, ColorError, ColorIdError
from .utils import is_color

from .spaces import *
