# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 - Martin Owens <doctormo@gmail.com>
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
Image element interface.
"""

import os
import urllib.request as urllib
import urllib.parse as urlparse
from base64 import encodebytes


from ..base import InkscapeExtension
from ..localization import inkex_gettext as _
from ._polygons import RectangleBase


class Image(RectangleBase):
    """Provide a useful extension for image elements"""

    tag_name = "image"

    @staticmethod
    def _get_type(path, header):
        """Basic magic header checker, returns mime type"""
        for head, mime in (
            (b"\x89PNG", "image/png"),
            (b"\xff\xd8", "image/jpeg"),
            (b"BM", "image/bmp"),
            (b"GIF87a", "image/gif"),
            (b"GIF89a", "image/gif"),
            (b"MM\x00\x2a", "image/tiff"),
            (b"II\x2a\x00", "image/tiff"),
        ):
            if header.startswith(head):
                return mime

        # ico files lack any magic... therefore we check the filename instead
        for ext, mime in (
            # official IANA registered MIME is 'image/vnd.microsoft.icon' tho
            (".ico", "image/x-icon"),
            (".svg", "image/svg+xml"),
        ):
            if path.endswith(ext):
                return mime
        return None

    def embed_image(self, file_path: str):
        """ "Embed the data of the selected Image Tag element.
        Relative image paths are interpreted relative to file_path.

        .. versionadded:: 1.5

        Args:
            file_path (str): Relative image paths are interpreted relative to file_path.
        """
        xlink = self.get("xlink:href")
        if xlink is not None and xlink[:5] == "data:":
            # No need, data already embedded
            return
        if xlink is None:
            raise AttributeError(
                _('Attribute "xlink:href" not set on node {}.'.format(self.get_id()))
            )

        url = urlparse.urlparse(xlink)
        href = urllib.url2pathname(url.path)

        # Look relative to the *temporary* filename instead of the original filename.
        try:
            cwd = os.path.dirname(file_path)
        except TypeError:
            # input_file was actually stdin, fall back.
            cwd = None
        path = InkscapeExtension.absolute_href(href or "", cwd=cwd)

        # Backup directory where we can find the image
        if not os.path.isfile(path):
            path = self.get("sodipodi:absref", path)

        if not os.path.isfile(path):
            raise ValueError(
                _('File not found "{}". Unable to embed image.').format(path)
            )
            return

        with open(path, "rb") as handle:
            # Don't read the whole file to check the header
            file_type = self._get_type(path, handle.read(10))
            handle.seek(0)

            if file_type:
                self.set(
                    "xlink:href",
                    "data:{};base64,{}".format(
                        file_type, encodebytes(handle.read()).decode("ascii")
                    ),
                )
                self.pop("sodipodi:absref")
            else:
                raise ValueError(
                    _(
                        "%s is not of type image/png, image/jpeg, "
                        "image/bmp, image/gif, image/tiff, or image/x-icon"
                    )
                    % path
                )
