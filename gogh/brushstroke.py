# brushstroke.py
# This file is part of Gogh Project
#
# Copyright (C) 2005, 2006, Aleksey Y. Nelipa
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
import math
from Numeric import *

from goghdoc import GoghDoc
from brushprovider import BrushProvider
from brushdata import BrushType
from goghutil import *

use_smudge = True

class DabRect:
    def __init__(self, x1, y1, x2, y2, brush_provider, pressure):
        self.brush_provider = brush_provider
        self.pressure = pressure
        brush_width, brush_height = self.brush_provider.get_brush_dimensions(self.pressure)
        self.x, self.y = int(floor(min(x1, x2)))-brush_width//2, int(floor(min(y1, y2)))-brush_height//2
        self.width, self.height = int(ceil(abs(x1-x2)))+brush_width, int(ceil(abs(y1-y2)))+brush_height
        self.alphas = zeros((self.height, self.width), Float)  
        
        
    def get_rectangle(self):
        return gtk.gdk.Rectangle(self.x, self.y, self.width, self.height)
        
    def put_brush(self, x, y):
        x-=self.x
        y-=self.y
        adj_brush = self.brush_provider.get_adjusted_brush(self.pressure, x-int(x), y-int(y))
        xt = int(floor(x))-adj_brush.shape[1]//2
        yt = int(floor(y))-adj_brush.shape[0]//2 
        alpha = self.brush_provider.brush_data.opacity_for_pressure(self.pressure)
        brush_dest = self.alphas[yt:yt+adj_brush.shape[0], xt:xt+adj_brush.shape[1]]
        brush_dest[...]=(1-(1-alpha*adj_brush)*(1-brush_dest))[...]
                
    def get_trimmed_pixbuf(self, color, doc_width, doc_height):
        x0, y0 = max(-self.x, 0), max(-self.y, 0)
        new_w = self.width-x0-max(self.x+self.width-doc_width, 0)
        new_h = self.height-y0-max(self.y+self.height-doc_height, 0)
        if new_w<=0 or new_h<=0:
            return None
        pixbuf = create_pixbuf(new_w, new_h)
        pixel_value = (color.red >> 8 << 16)+(color.green >> 8 << 8)+(color.blue >> 8)
        pixel_value <<= 8
        pixbuf.fill(pixel_value)
        pixbuf.get_pixels_array()[:,:,3] = (255*self.alphas[y0:y0+new_h, x0:x0+new_w]).astype(UInt8)
        return pixbuf
        
class AbstractBrushStroke:
    def __init__(self, goghview, current_layer_key):
        self.goghview = goghview
        self.goghdoc = self.goghview.goghdoc
        self.current_layer_key = current_layer_key
         
    def start_draw(self, x, y): 
        if len(self.goghdoc.layers) == 0 :
            return
        self.last_x = x
        self.last_y = y
        self.offset = 0          
       
    def draw_to(self, x, y, pressure):
        if(len(self.goghdoc.layers) == 0):
            return
        delta_x = x-self.last_x
        delta_y = y-self.last_y
        if delta_x==0 and delta_y :
            return
        h = math.hypot(delta_x, delta_y)
        intermediate_points = arange(self.offset, h, self.brush_options.step)
        intermediate_coords = [(self.last_x+delta_x*t/h, self.last_y+delta_y*t/h) for t in intermediate_points]
        self.apply_brush_stroke(self.last_x, self.last_y, x, y, intermediate_coords, pressure)
        if len(intermediate_points)>0 :
            self.offset = self.brush_options.step-(h-intermediate_points[-1])
        else :
            self.offset -= h
        self.last_x, self.last_y = x, y
    
    def apply_brush_stroke(self, x0, y0, x1, y1, intermediate_coords, pressure):
        raise NotImplementedError('Must be implemented in subclass')
  
        
class BrushStroke (AbstractBrushStroke):
    def __init__(self, goghview, current_layer_key, color, brush_options):
        AbstractBrushStroke.__init__(self, goghview, current_layer_key)
        self.color = color
        self.brush_options = brush_options
        self.bounding_rectangle = None
        self.brush_provider = BrushProvider(brush_options)        
    
    def put_dab_on_layer(self, pressure):    
        opacity = self.brush_options.opacity_for_pressure(pressure)
        dab_pixbuf = self.dab_rect.get_trimmed_pixbuf(self.color, self.goghdoc.width, self.goghdoc.height)
        if not dab_pixbuf:
            return
        x, y = max(0, self.dab_rect.x), max(0, self.dab_rect.y)
        if self.brush_options.brush_type == BrushType.Eraser :
            self.goghdoc.subtract_alpha(dab_pixbuf, x, y, 1, self.current_layer_key);
        else:
            self.goghdoc.put_pixbuf_on_layer(dab_pixbuf, x, y, 1, self.current_layer_key);
        self.goghview.update_view_pixbuf(x, y, dab_pixbuf.get_width(), dab_pixbuf.get_height())
        self.goghview.redraw_image_fragment_for_model_coord(x, y, dab_pixbuf.get_width(), dab_pixbuf.get_height())
            
    def expand_bounding_rectangle(self, new_rect):
        if self.bounding_rectangle :
            self.bounding_rectangle = self.bounding_rectangle.union(new_rect)
        else:
            self.bounding_rectangle = new_rect.copy()
        self.bounding_rectangle = self.bounding_rectangle.intersect(gtk.gdk.Rectangle(0, 0, self.goghdoc.width, self.goghdoc.height))
    
    def apply_brush_stroke(self, x0, y0, x1, y1, intermediate_coords, pressure):
        self.dab_rect = DabRect(x0, y0, x1, y1, self.brush_provider, pressure)        
        self.expand_bounding_rectangle(self.dab_rect.get_rectangle())
        for x, y in intermediate_coords:
            self.dab_rect.put_brush(x, y)  
        self.put_dab_on_layer(pressure)    
                               
        
        
