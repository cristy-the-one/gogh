# gpghview.py
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

from Numeric import *
import gtk.gdk

from goghutil import *
from observer import Observer

class GoghView:
    def __init__(self, goghdoc, drawable):
        self.x_visible, self.y_visible, self.w_visible, self.h_visible = 0, 0, 0, 0
        self.pixbuf0 = None
        self.goghdoc = goghdoc
        self.drawable = drawable
        self.zoom_factor = 1.0
        self.size_observer = Observer()
        self.image_observer = Observer()
        self.reset_view_pixbuf()
        self.goghdoc.size_observer.add_callback(self.reset_view_pixbuf)
        self.goghdoc.pixbuf_observer.add_callback(self.refresh_area)
        self.gc = self.drawable.new_gc()

        
    def get_size(self):
        return int(ceil(self.goghdoc.width*self.zoom_factor)), int(ceil(self.goghdoc.height*self.zoom_factor))
        
        
    def zoom_in(self):
        self.set_zoom(self.zoom_factor*1.5)
        self.size_observer.notify_all()
        
    def zoom_out(self):
        self.set_zoom(self.zoom_factor/1.5)
        self.size_observer.notify_all()

    def set_zoom(self, zoom_factor):
        self.zoom_factor = zoom_factor
        if abs(self.zoom_factor-round(self.zoom_factor))<0.01:
            self.zoom_factor = round(self.zoom_factor)
        self.reset_view_pixbuf()
       
    def update_view_pixbuf(self, x, y, w, h):
        xv, yv, wv, hv = self.to_view_rect(x, y, w, h)
        self.goghdoc.composite.scale(self.pixbuf0, xv-self.x_visible, yv-self.y_visible, wv, hv, -self.x_visible, -self.y_visible, self.zoom_factor, self.zoom_factor, gtk.gdk.INTERP_TILES)
        #self.goghdoc.composite.scale(self.pixbuf, xv, yv, wv, hv, 0, 0, self.zoom_factor, self.zoom_factor, gtk.gdk.INTERP_TILES) 
        
    def reset_view_pixbuf(self):
        #w, h = self.get_size()
        #self.pixbuf = self.goghdoc.composite.scale_simple(w, h, gtk.gdk.INTERP_TILES)
        if self.pixbuf0 :
            if (self.pixbuf0.get_width(), self.pixbuf0.get_height()) != (self.w_visible +1, self.h_visible+1):
                del self.pixbuf0
                self.pixbuf0 = create_pixbuf(self.w_visible +1, self.h_visible+1)
        else :
            self.pixbuf0 = create_pixbuf(self.w_visible +1, self.h_visible+1)
        self.goghdoc.composite.scale(self.pixbuf0, 0, 0, self.w_visible +1, self.h_visible+1, -self.x_visible, -self.y_visible, self.zoom_factor, self.zoom_factor, gtk.gdk.INTERP_TILES)
        #self.size_observer.notify_all()
                
    def refresh_area(self, area_rect=None):
        if not area_rect:
            self.reset_view_pixbuf()        
            self.image_observer.notify_all(gtk.gdk.Rectangle(0, 0, self.w_visible, self.h_visible))
            return
        xv, yv, wv, hv = self.to_view_rect(area_rect.x, area_rect.y, area_rect.width, area_rect.height)
        self.goghdoc.composite.scale(self.pixbuf0, xv-self.x_visible, yv-self.y_visible, wv, hv, -self.x_visible, -self.y_visible, self.zoom_factor, self.zoom_factor, gtk.gdk.INTERP_TILES) 
        #self.goghdoc.composite.scale(self.pixbuf, xv, yv, wv, hv, 0, 0, self.zoom_factor, self.zoom_factor, gtk.gdk.INTERP_TILES) 
        self.image_observer.notify_all(gtk.gdk.Rectangle(xv, yv, wv, hv))
        
        
    def to_model(self, x, y):
        return x/self.zoom_factor, y/self.zoom_factor
        
    def to_view(self, x, y):
        return x*self.zoom_factor, y*self.zoom_factor
        
    def redraw_image_fragment_for_model_coord(self, x, y, w, h):
        if self.zoom_factor==1:
            self.drawable.draw_pixbuf(self.gc, self.goghdoc.composite, x, y, x, y, w, h)   
            return            
        xv, yv, wv, hv = self.to_view_rect(x, y, w, h)
        self.drawable.draw_pixbuf(self.gc, self.pixbuf0, xv-self.x_visible, yv-self.y_visible, xv, yv, wv, hv) 
        #self.drawable.draw_pixbuf(self.gc, self.pixbuf, xv, yv, xv, yv, wv, hv)      
        
    def to_view_rect(self, x, y, w, h):
        xv1, yv1 = map(lambda(t): int(floor(t)), self.to_view(x, y))
        xv2, yv2 = map(lambda(t): int(ceil(t)), self.to_view(x+w, y+h))  
        return  xv1, yv1, xv2-xv1, yv2-yv1
        
    def reposition(self, x, y, w, h):
        if (self.x_visible, self.y_visible) == (x, y, w, h):
           return 
        self.x_visible, self.y_visible, self.w_visible, self.h_visible = map(lambda k: int(k), (x, y, w, h))
        
        
        
        
        
    
