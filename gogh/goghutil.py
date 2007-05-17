# goghutil.py
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
import time
import re
import os.path
from Numeric import *

def get_pixels_from_pixbuf(pixbuf, rect):
    return pixbuf.get_pixels_array()[rect.y:rect.y+rect.height, rect.x:rect.x+rect.width,:]

def put_pixbuf_on_pixbuf(src, dest, x, y, alpha):
    alpha256 = int(round(255*alpha))
    src.composite(dest, x, y, src.get_width(), src.get_height(), x, y, 1, 1, gtk.gdk.INTERP_NEAREST, alpha256)

def copy_pixbuf_on_pixbuf(src, dest, x, y):
    src.copy_area(0, 0, src.get_width(), src.get_height(), dest, x, y)

def subtract_alpha(src, dest, x, y, alpha):
    w = min(src.get_width(), dest.get_width()-x)
    h = min(src.get_height(), dest.get_height()-y)    
    dest_alphas = dest.get_pixels_array()[y:y+h,x:x+w,3]
    src_alphas = (src.get_pixels_array()[0:h,0:w,3]*alpha)
    dest_alphas[:,:] = maximum(0, (dest_alphas - src_alphas)).astype(UInt8)[:,:]

def create_pixbuf(w, h):
    return gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, w, h)    
    
def find_item(itemlist, criterion):
    for item in itemlist:
        if criterion(item) :
            return item
    return None
    
def find_index(itemlist, criterion):
    for i in range(0, len(itemlist)):
        if criterion(itemlist[i]):
            return i;
    return None
    
def copy_onto(src, dest, x, y):
    xs1, ys1 = max(0, -x), max(0, -y)
    xs2, ys2 = min(src.shape[1], dest.shape[1]-x), min(src.shape[0], dest.shape[0]-y)
    if xs1>=xs2 or ys1>=ys2:
        return
    xd1, yd1 = max(x, 0), max(y, 0)
    xd2, yd2 = min(dest.shape[1], src.shape[1]+x), min(dest.shape[0], src.shape[0]+y)
    dest[yd1:yd2, xd1:xd2, ...] = src[ys1:ys2, xs1:xs2, ...]
    
def swap_items(itemlist, i, j):
    itemlist[i], itemlist[j] = itemlist[j], itemlist[i]
    
def shift_array_down(a, x):
    b = a[:-1]*x
    c = a*(1-x)
    add(c[1:], b, c[1:])
    return c
    
def shift_array_right(a, x):
    b = a[:,:-1]*x
    c = a*(1-x)
    add(c[:,1:], b, c[:,1:])
    return c
    
def replace_extension(s, ext):
    return re.sub('(\.[^\.]*$)|($)', '.'+ext, s)
    
def rect_to_list(r):
    return [r.x, r.y, r.width, r.height]
    
def rect_from_list(r):
    return gtk.gdk.Rectangle(r[0], r[1], r[2], r[3])
    
def inverse_dictionary(dictionary):
    inv_dict = {}
    for key in dictionary:
        inv_dict[dictionary[key]]=key
    return inv_dict    
    
def get_abspath(path):
    return os.path.join(os.path.dirname(__file__), path)
    
class PixbufSerializer:
    def __init__(self) :
        pass
        
    def append_to_result(self, buf) :
        self.result += buf
        
    def save_pixbuf(self, pixbuf) :
        self.result = ""
        pixbuf.save_to_callback(self.append_to_result, "png")
        return self.result
        
    def load_pixbuf(self, buf) :
        loader = gtk.gdk.PixbufLoader()
        loader.write(buf, len(buf))
        loader.close()
        return loader.get_pixbuf()

  
