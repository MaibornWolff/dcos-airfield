# -*- coding: utf-8 -*-
"""Various helper scripts for serialization."""

import re


def serialize_enum(enum_object):
    serialized_enum = {}
    for element in enum_object:
        serialized_enum[element.name] = element.value
    return serialized_enum


def clean_input_string(line: str) -> str:
    return re.sub('[!@#$&?%*+:;,/]', '', line)

