# resizedialog.py
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

from command import ResizeAction

class ResizeDialog:
    def __init__(self):
        xml = gtk.glade.XML("glade/goghglade.glade", root="resize_document_dialog")
        xml.signal_autoconnect(self)  
        self.dialog = xml.get_widget("resize_document_dialog")
        self.preview_area = xml.get_widget("preview_drawing_area")
        self.left_spin = xml.get_widget("left_spin")
        self.top_spin = xml.get_widget("top_spin")
        self.right_spin = xml.get_widget("right_spin")
        self.bottom_spin = xml.get_widget("bottom_spin")
        self.all_spins = (self.left_spin, self.top_spin, self.right_spin, self.bottom_spin)
        self.adjustments = (0, 0, 0, 0)


    def set_document(self, goghdoc):
        self.goghdoc = goghdoc
        
    def reset_spins(self):
        for spin in self.all_spins:
            spin.set_value(0)        
        
    def show(self):
        self.reset_spins()
        response = self.dialog.run()
        if response == gtk.RESPONSE_OK :
            self.resize_document()
            self.dialog.hide()
        if response == gtk.RESPONSE_APPLY :
            self.resize_document()
            self.show()
        if response == gtk.RESPONSE_CANCEL :
            self.dialog.hide()   

        
    def resize_document(self):
        resize_action = ResizeAction(self.goghdoc, self.adjustments)
        self.goghdoc.command_stack.add(resize_action)        
        
       
    def on_spin_value_changed(self, widget, data=None):
        self.preview_area.window.invalidate_rect(None, False)
        self.adjustments = map(lambda spin: spin.get_value_as_int(), self.all_spins)
        
        
    def on_preview_drawing_area_expose_event(self, widget, data=None):
        drawable = self.preview_area.window
        area_w, area_h = drawable.get_size()
        
        rect_bounds = gtk.gdk.Rectangle(0, 0, self.goghdoc.width, self.goghdoc.height)
        new_bounds = rect_bounds.copy()
        new_bounds.x -= self.left_spin.get_value_as_int()
        new_bounds.y -= self.top_spin.get_value_as_int()
        new_bounds.width += -new_bounds.x + self.right_spin.get_value_as_int()
        new_bounds.height += -new_bounds.y + self.bottom_spin.get_value_as_int()
        
        k = min(area_w/self.goghdoc.width, area_h/self.goghdoc.height)*0.5
        w, h = int(self.goghdoc.width*k), int(self.goghdoc.height*k)
        x0, y0 = (area_w-w)//2, (area_h-h)//2
        scaled_composite = self.goghdoc.composite.scale_simple(w, h, gtk.gdk.INTERP_BILINEAR)
        gc = drawable.new_gc()
        drawable.draw_pixbuf(gc, scaled_composite, 0, 0, x0, y0)
        drawable.draw_rectangle(gc, False, x0+int(new_bounds.x*k), y0+int(new_bounds.y*k), int(new_bounds.width*k), int(new_bounds.height*k))
        
    def on_resize_document_dialog_delete_event(self, widget, data=None):
        self.dialog.hide()
        return True
