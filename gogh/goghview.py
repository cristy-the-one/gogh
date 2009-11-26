# gpghview.py
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

from numpy import *
import gtk.gdk

from goghutil import *
from observer import Observer

class GoghView:
    def __init__(self, goghdoc, drawable):
        self.x_visible, self.y_visible, self.w_visible, self.h_visible = 0, 0, 0, 0
        self.viewpixbuf = None
        self.goghdoc = goghdoc
        self.drawable = drawable
        self.zoom_factor = 1.0
        self.size_observer = Observer()
        self.image_observer = Observer()
        self.goghdoc.size_observer.add_callback(self.on_resize)
        self.goghdoc.pixbuf_observer.add_callback(self.refresh_area)
        self.gc = self.drawable.new_gc()
        self.top_level_gc = self.drawable.new_gc(function=gtk.gdk.INVERT)
        self.show_cursor = False
        self.xcur, self.ycur, self.brush_min_width, self.brush_max_width = 0, 0, 0, 0
        self.xcur_old, self.ycur_old = None, None


    def get_size(self):
        return int(ceil(self.goghdoc.width*self.zoom_factor)), int(ceil(self.goghdoc.height*self.zoom_factor))


    def zoom_in(self):
        self.set_zoom(self.zoom_factor*1.5)

    def zoom_out(self):
        self.set_zoom(self.zoom_factor/1.5)

    def zoom_normal(self):
        self.set_zoom(1.0)

    def set_zoom(self, zoom_factor):
        self.zoom_factor = zoom_factor
        if abs(self.zoom_factor-round(self.zoom_factor))<0.01:
            self.zoom_factor = round(self.zoom_factor)
        self.size_observer.notify_all()


    def scale_with_clipping(self, x, y, w, h):
        if x<0 :
            w,x = w-x, 0
        if x+w>self.viewpixbuf.get_width() :
            w = self.viewpixbuf.get_width()-x
        if y<0 :
            h, y = h-y, 0
        if y+h>self.viewpixbuf.get_height() :
            h = self.viewpixbuf.get_height()-y
        if w<=0 or h<=0 :
            return
        self.goghdoc.composite.scale(self.viewpixbuf, x, y, w, h, -self.x_visible, -self.y_visible, self.zoom_factor, self.zoom_factor, gtk.gdk.INTERP_TILES)

    def update_view_pixbuf(self, x, y, w, h):
        xv, yv, wv, hv = self.to_view_rect(x, y, w, h)
        self.scale_with_clipping(xv-self.x_visible, yv-self.y_visible, wv, hv)

    def reset_view_pixbuf(self):
        if self.viewpixbuf :
            if (self.viewpixbuf.get_width(), self.viewpixbuf.get_height()) != (self.w_visible +1, self.h_visible+1):
                del self.viewpixbuf
                self.viewpixbuf = create_pixbuf(self.w_visible +1, self.h_visible+1)
        else :
            self.viewpixbuf = create_pixbuf(self.w_visible +1, self.h_visible+1)
        self.scale_with_clipping(0, 0, self.w_visible +1, self.h_visible+1)

    def refresh_area(self, area_rect=None):
        if not area_rect:
            self.image_observer.notify_all(gtk.gdk.Rectangle(0, 0, self.w_visible, self.h_visible), False)
            return
        xv, yv, wv, hv = self.to_view_rect(area_rect.x, area_rect.y, area_rect.width, area_rect.height)
        self.scale_with_clipping(xv-self.x_visible, yv-self.y_visible, wv, hv)
        self.image_observer.notify_all(gtk.gdk.Rectangle(xv, yv, wv, hv), False)

    def on_resize(self):
        self.reset_view_pixbuf()
        self.size_observer.notify_all()


    def to_model(self, x, y):
        return x/self.zoom_factor, y/self.zoom_factor

    def to_view(self, x, y):
        return x*self.zoom_factor, y*self.zoom_factor

    def redraw_image_fragment_for_model_coord(self, x, y, w, h):
        xv, yv, wv, hv = self.to_view_rect(x, y, w, h)
        if self.zoom_factor==1:
            self.draw_pixbuf_with_clipping(self.goghdoc.composite, xv, yv, xv, yv, wv, hv)
        else:
            xv, yv, wv, hv = xv-1, yv-1, wv+2, hv+2
            self.draw_pixbuf_with_clipping(self.viewpixbuf, xv-self.x_visible, yv-self.y_visible, xv, yv, wv, hv)
        self.draw_top_level_items(xv, yv, wv, hv)

    def draw_pixbuf_with_clipping(self, pixbuf, src_x, src_y, dest_x, dest_y, w, h):
        w_ofs, h_ofs = min(src_x, 0), min(src_y, 0)
        w_cutoff, h_cutoff = max(src_x+w-pixbuf.get_width(), 0), max(src_y+h-pixbuf.get_height(), 0)
        if w<=w_ofs+w_cutoff or h<=h_ofs+h_cutoff:
            return
        self.drawable.draw_pixbuf(self.gc, pixbuf, src_x-w_ofs, src_y-h_ofs, dest_x-w_ofs, dest_y-h_ofs, w-w_ofs-w_cutoff, h-h_ofs-h_cutoff)

    def redraw_image_for_cursor(self):
        max_size = max(self.brush_min_width, self.brush_max_width)+1
        d = max_size//2
        model_rect = None
        if self.xcur_old is not None and self.ycur_old is not None:
            model_rect = rect_union(model_rect, rect_from_float_list([self.xcur_old-d, self.ycur_old-d-1, max_size+2, max_size+2]))
        if self.show_cursor:
            model_rect = rect_union(model_rect, rect_from_float_list([self.xcur-d-1, self.ycur-d-1, max_size+2, max_size+2]))
        if model_rect:
            model_rect = model_rect.intersect(gtk.gdk.Rectangle(0, 0, self.goghdoc.width, self.goghdoc.height))
            self.redraw_image_fragment_for_model_coord(model_rect.x, model_rect.y, model_rect.width, model_rect.height)
        self.xcur_old, self.ycur_old = self.xcur, self.ycur


    def draw_top_level_items(self, xv, yv, wv, hv):
        self.top_level_gc.set_clip_rectangle(gtk.gdk.Rectangle(xv, yv, wv, hv))
        if self.show_cursor:
            xc, yc = [int(round(t)) for t in self.to_view(self.xcur, self.ycur)]
            w1, w2 = [int(ceil(w*self.zoom_factor)) | 1 for w in (self.brush_min_width, self.brush_max_width)]
            self.drawable.draw_arc(self.top_level_gc, False, xc-w1//2, yc-w1//2, w1, w1, 0, 360*64)
            if w1 != w2:
                self.drawable.draw_arc(self.top_level_gc, False, xc-w2//2, yc-w2//2, w2, w2, 0, 360*64)

    def to_view_rect(self, x, y, w, h):
        xv1, yv1 = [int(floor(t)) for t in self.to_view(x, y)]
        xv2, yv2 = [int(ceil(t)) for t in self.to_view(x+w, y+h)]
        return  xv1, yv1, xv2-xv1, yv2-yv1

    def reposition(self, x, y, w, h):
        if (self.x_visible, self.y_visible, self.w_visible, self.h_visible) == (x, y, w, h):
           return
        self.x_visible, self.y_visible, self.w_visible, self.h_visible = [int(k) for k in (x, y, w, h)]

    def redraw_image(self):
        self.reset_view_pixbuf()
        self.drawable.draw_pixbuf(self.drawable.new_gc(), self.viewpixbuf, 0, 0, self.x_visible, self.y_visible, -1, -1)
        self.draw_top_level_items(self.x_visible, self.y_visible, self.w_visible, self.h_visible)

    def set_cursor(self, x, y, brush_data):
        self.xcur, self.ycur, self.brush_min_width, self.brush_max_width = x, y, brush_data.min_width, brush_data.max_width
        self.show_cursor = True

    def set_no_cursor(self):
        self.show_cursor = False
