# brushprovider.py
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

import math
from Numeric import *

from goghutil import *

num_sub_pixel = 4

class BrushProvider:
    def __init__(self, brush_data):
        self.brushes_for_size = {}
        self.brush_data = brush_data


    def create_brush(self, pressure):
        size = self.get_brush_dimensions(pressure)[0]
        center = int(ceil(size/2))
        brush_alphas = zeros((size, size), Float)
        brush_segment =  fromfunction(lambda x,y : self.alpha_for_point(x, y, size, self.get_rounded_brush_size(pressure)/2), (center, center))
        brush_alphas[:center, :center] = brush_segment[:,:]
        brush_alphas[:center, -1:-center-1:-1] = brush_alphas[:center, :center]
        brush_alphas[-1:-center-1:-1,:] = brush_alphas[:center,:]
        return brush_alphas


    def get_adjusted_brush(self, pressure, dx, dy):
        dx = round(dx*num_sub_pixel)/num_sub_pixel
        dy = round(dy*num_sub_pixel)/num_sub_pixel
        adj_size = self.get_rounded_brush_size(pressure)
        if(self.brushes_for_size.has_key((adj_size, 0, 0))):
            adj_brush = self.brushes_for_size[(adj_size, 0, 0)]
        else:
            adj_brush = self.create_brush(pressure)
            self.brushes_for_size[(adj_size, 0, 0)] = adj_brush
        adj_brush = self.get_shifted_brush(adj_size, dx, dy)
        return adj_brush

    def get_shifted_brush(self, size, dx, dy):
        if(self.brushes_for_size.has_key((size, dx, dy))):
            return self.brushes_for_size[(size, dx, dy)].copy()
        if(self.brushes_for_size.has_key((size, dx, 0))):
            brush_alphas = self.brushes_for_size[(size, dx, 0)].copy()
        else :
            brush_alphas = shift_array_right(self.brushes_for_size[(size, 0, 0)], dx)
            self.brushes_for_size[(size, dx, 0)] = brush_alphas.copy()
        brush_alphas = shift_array_down(brush_alphas, dy)
        self.brushes_for_size[(size, dx, dy)] = brush_alphas.copy()
        return brush_alphas

    def get_brush_dimensions(self, pressure):
        sz = int(floor(self.get_rounded_brush_size(pressure)/2)*2+1)
        return sz, sz

    def get_max_brush_dimensions(self):
        return max(self.get_brush_dimensions(0), self.get_brush_dimensions(1))

    def get_rounded_brush_size(self, pressure):
        sz = self.brush_data.size_for_pressure(pressure)+2
        if sz>10:
            return round(sz)
        if sz>5:
            return round(sz*2)/2
        return round(sz*4)/4


    def alpha_for_point(self, x, y, size, span):
        center = size/2
        d_sq = ((x-center)**2+(y-center)**2)
        hsz_sq = span**2
        return minimum(1, 1.2*maximum(0,1-d_sq/hsz_sq))





