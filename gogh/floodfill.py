# floodfill.py
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

from copy import copy

from goghutil import *
from command import EditLayerAction

import time

def create_flood_fill_action(goghdoc, layer_key, start_x, start_y, color):
    threshold_sq = 200**2
    layer_pixbuf = goghdoc.layer_for_key(layer_key).pixbuf
    original_pixbuf = layer_pixbuf.copy()
    list = [(int(start_x), int(start_y))]
    min_x, max_x = int(start_x), int(start_x)
    min_y, max_y = int(start_y), int(start_y)
    original_color = layer_pixbuf.get_pixels_array()[int(start_y), int(start_x), 0:3].astype(UInt32)
    original_color = copy.copy(original_color)
    pixels = layer_pixbuf.get_pixels_array()
    c1, c2, c3, c4, c5, c6 = 0, 0, 0, 0, 0, 0
    time1 = time.time()
    #print ((original_color[0]-pixels[:, :, 0])**2)
    #print ((original_color[0]-pixels[:, :, 0])**2)*pixels[:,:,3]
    #print ((original_color[0]-pixels[:, :, 0])**2)*pixels[:,:,3]/255.
    #print sqrt(((original_color[0]-pixels[:, :, 0])**2)*pixels[:,:,3]/255.)
    #print sqrt(((original_color[0]-pixels[:, :, 0])**2))*pixels[:,:,3]/255.
    #print ((original_color[0]-pixels[:, :, 0])**2 + (original_color[1]-pixels[:, :, 1])**2 + (original_color[2]-pixels[:, :, 2])**2)*pixels[:, :, 3]
    #candidates = where(((original_color[0]-pixels[:, :, 0])**2 + (original_color[1]-pixels[:, :, 1])**2 + (original_color[2]-pixels[:, :, 2])**2)*(pixels[:, :, 3]**2) < 255*255*threshold_sq, 1, 0)
    candidates = where((original_color[0]-pixels[:,:,0])**2<threshold_sq and pixels[:,:,3]<200, 1, 0)
    marks = zeros(candidates.shape)
    while len(list)>0:
        timeA = time.time()
        x, y = list.pop()
        c5 = c5 + time.time()-timeA
        timeA = time.time()
        if x < min_x:
            min_x = x
        if x > max_x:
            max_x = x
        if y < min_y:
            min_y = y
        if y > max_y:
            max_y = y
        c6 = c6 + time.time()-timeA
        timeA = time.time()
        if marks[y,x] or not candidates[y, x]:
            c2 = c2 + time.time()-timeA
            continue
        c2 = c2 + time.time()-timeA
        timeA = time.time()
        marks[y, x] = 1
        c3 = c3 + time.time()-timeA
        c1 = c1 + 1
        timeA = time.time()
        if x>0:
            list.append([x-1, y])
        if x<goghdoc.width-1:
            list.append([x+1, y])
        if y>0:
            list.append([x, y-1])
        if y<goghdoc.height-1:
            list.append([x, y+1])
        c4 = c4 + time.time()-timeA
    red, green, blue = [c>>8 for c in [color.red, color.green, color.blue]]
    pixels[:,:,0] = ((1-marks)*pixels[:,:,0] + marks*red).astype(UInt8)[:,:]
    pixels[:,:,1] = ((1-marks)*pixels[:,:,1] + marks*green).astype(UInt8)[:,:]
    pixels[:,:,2] = ((1-marks)*pixels[:,:,2] + marks*blue).astype(UInt8)[:,:]
    pixels[:,:,3] = ((1-marks)*pixels[:,:,3] + marks*255).astype(UInt8)[:,:]
    time2 = time.time()
    print c1, time2-time1, c2, c3, c4, c5, c6
    goghdoc.reset_composite()
    edit_area = gtk.gdk.Rectangle(min_x, min_y, max_x-min_x, max_y-min_y)
    return EditLayerAction(goghdoc, layer_key, original_pixbuf, edit_area) 



