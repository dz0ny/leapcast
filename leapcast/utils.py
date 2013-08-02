# -*- coding: utf8 -*-

from __future__ import unicode_literals
import string
from textwrap import dedent


def render(template):
    return string.Template(dedent(template))
