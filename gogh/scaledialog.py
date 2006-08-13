# scaledialog.py
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

from command import ScaleAction

class ScaleDialog:
    def __init__(self):
        xml = gtk.glade.XML("glade/goghglade.glade", root="scale_document_dialog")
        xml.signal_autoconnect(self)  
        self.suspend_width_spin_change = False
        self.suspend_height_spin_change = False
        self.goghdoc = None
        self.dialog = xml.get_widget("scale_document_dialog")
        self.width_spin = xml.get_widget("width_spin")
        self.height_spin = xml.get_widget("height_spin")
        self.proportional_scale_checkbutton = xml.get_widget("proportional_scale_checkbutton")
        self.scale_type_combobox = xml.get_widget("scale_type_combobox")
        self.scale_type_combobox.set_active(0)

    def set_document(self, goghdoc):
        self.goghdoc = goghdoc
        
      
    def show(self):
        self.scale_type_combobox.set_active(0)
        self.proportional_scale_checkbutton.set_active(True)
        self.width_spin.set_value(self.goghdoc.width)
        self.height_spin.set_value(self.goghdoc.height)
        response = self.dialog.run()
        if response == gtk.RESPONSE_OK :
            self.scale_document()
            self.dialog.hide()
        if response == gtk.RESPONSE_CANCEL :
            self.dialog.hide()   

        
    def scale_document(self):
        if self.scale_type_combobox.get_active() == 0 :
            w = self.width_spin.get_value_as_int()
            h = self.height_spin.get_value_as_int()
        else :
            w = self.width_spin.get_value_as_int()*self.goghdoc.width//100
            h = self.height_spin.get_value_as_int()*self.goghdoc.height//100
        scale_action = ScaleAction(self.goghdoc, w, h)
        self.goghdoc.command_stack.add(scale_action)        
       
       
    def on_scale_document_dialog_delete_event(self, widget, data=None):
        self.dialog.hide()
        return True
        
    def on_width_spin_changed(self, widget, data=None):
        if  self.width_spin.get_text() == "" or self.width_spin.get_text().startswith('0'):
            return
        self.width_spin.update()
        if self.proportional_scale_checkbutton.get_active() and not self.suspend_height_spin_change:
            w = self.width_spin.get_value_as_int()
            if self.scale_type_combobox.get_active() == 0 :
                h = int(round(self.goghdoc.height*w/self.goghdoc.width))
            else :
                h = w
            if h != self.height_spin.get_value_as_int() :
                self.suspend_width_spin_change = True
                self.height_spin.set_value(h)
                self.suspend_width_spin_change = False
       
    def on_height_spin_changed(self, widget, data=None):
        if self.height_spin.get_text() == "" or self.height_spin.get_text().startswith('0'):
            return
        self.height_spin.update()
        if self.proportional_scale_checkbutton.get_active() and not self.suspend_width_spin_change :
            h = self.height_spin.get_value_as_int()
            if self.scale_type_combobox.get_active() == 0 :
                w = int(round(self.goghdoc.width*h/self.goghdoc.height))
            else :
                w = h  
            if w != self.width_spin.get_value_as_int() :
                self.suspend_height_spin_change = True
                self.width_spin.set_value(w)
                self.suspend_height_spin_change = False
        
    def on_proportional_scale_checkbutton_toggled(self, widget, data=None):
        pass
    
    def on_scale_type_combobox_changed(self, widget, data=None):
        if not self.goghdoc:
            return 
        if self.scale_type_combobox.get_active() == 0 :
            w_pixels = self.width_spin.get_value_as_int()*self.goghdoc.width//100
            h_pixels = self.height_spin.get_value_as_int()*self.goghdoc.height//100
            self.width_spin.set_value(w_pixels)
            self.height_spin.set_value(h_pixels)
        if self.scale_type_combobox.get_active() == 1 :
            w_percent = self.width_spin.get_value_as_int()*100//self.goghdoc.width
            h_percent = self.height_spin.get_value_as_int()*100//self.goghdoc.height
            self.width_spin.set_value(w_percent)
            self.height_spin.set_value(h_percent)


