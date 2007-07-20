# brushdata.py
# This file is part of Gogh Project
#
# Copyright (C) 2005-2007, Aleksey Y. Nelipa
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
# Foundation, Inc., 59 Temple Place, Suite 330,
# Boston, MA 02111-1307, USA.

from __future__ import division

import gtk
import gtk.gdk
import gtk.glade
import copy

class BrushType:
    Pen, Eraser, Smudge = range(3)

class BrushData:
    def __init__(self, name = _("Custom"), min_width = 1, max_width=4, min_opacity=0, max_opacity=1, step=1, smudge_amount=0.5, brush_type = BrushType.Pen):
        self.name = name
        self.min_width = int(min_width)
        self.max_width = int(max_width)
        self.min_opacity = min_opacity
        self.max_opacity = max_opacity
        self.brush_type = brush_type
        self.step = step
        self.smudge_amount = 0.5
        self.populate_originals()
        self.is_original = True

    def size_for_pressure(self, pressure):
        return self.min_width + (self.max_width - self.min_width) * pressure

    def opacity_for_pressure(self, pressure):
        return self.min_opacity + (self.max_opacity - self.min_opacity) * pressure

    def restore_from_originals(self):
        self.min_width, self.max_width, self.min_opacity, self.max_opacity, self.brush_type, self.step, self.smudge_amount = self.originals

    def populate_originals(self):
        self.originals = [self.min_width, self.max_width, self.min_opacity, self.max_opacity, self.brush_type, self.step, self.smudge_amount]

    def create_copy(self):
        new_brush_data = copy.copy(self)
        new_brush_data.is_original = False
        new_brush_data.populate_originals()
        return new_brush_data




