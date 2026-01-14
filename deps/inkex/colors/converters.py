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
"""
Basic color errors and common functions
"""

from collections import defaultdict

from typing import Dict, List, Callable

ConverterFunc = Callable[[float], List[float]]


class Converters:
    """
    Record how colors can be converted between different spaces and provides
    a way to path-find between multiple step conversions.
    """

    links: Dict[str, Dict[str, ConverterFunc]] = defaultdict(dict)
    chains: Dict[str, List[List[str]]] = {}

    @classmethod
    def add_space(cls, color_cls):
        """
        Records the stated links between this class and other color spaces
        """
        for name, func in color_cls.__dict__.items():
            if not name.startswith("convert_"):
                continue
            _, direction, space = name.split("_", 2)
            from_name = color_cls.name if direction == "to" else space
            to_name = color_cls.name if direction == "from" else space

            if from_name != to_name:
                if not isinstance(func, staticmethod):
                    raise TypeError(f"Method '{name}' must be a static method.")
                cls.links[from_name][to_name] = func.__func__

    @classmethod
    def get_chain(cls, source, target):
        """
        Get a chain of conversions between two color spaces, if possible.
        """

        def build_chains(chains, space):
            new_chains = []
            for chain in chains:
                for hop in cls.links[space]:
                    if hop not in chain:
                        new_chains += build_chains([chain + [hop]], hop)
            return chains + new_chains

        if source not in cls.chains:
            cls.chains[source] = build_chains([[source]], source)

        chosen = None
        for chain in cls.chains[source] or ():
            if chain[-1] == target and (not chosen or len(chain) < len(chosen)):
                chosen = chain
        return chosen

    @classmethod
    def find_converter(cls, source, target):
        """
        Find a way to convert from source to target using any conversion functions.

        Will hop from one space to another if needed.
        """
        func = None

        # Passthough
        if source == target:
            return lambda self: self

        if func is None:
            chain = cls.get_chain(source.name, target.name)
            if chain:
                return cls.generate_converter(chain, source, target)

        # Returning a function means we only run this function once, even when not found
        def _error(self):
            raise NotImplementedError(
                f"Color space {source} can not be converted to {target}."
            )

        return _error

    @classmethod
    def generate_converter(cls, chain, source_cls, target_cls):
        """
        Put together a function that can do every step of the chain of conversions
        """
        # Build a list of functions to run
        funcs = [cls.links[a][b] for a, b in zip(chain, chain[1:])]
        funcs.insert(0, source_cls.to_units)
        funcs.append(target_cls.from_units)

        def _inner(values):
            if hasattr(values, "alpha") and values.alpha is not None:
                values = list(values) + [values.alpha]
            for func in funcs:
                values = func(*values)
            return target_cls(values)

        return _inner
