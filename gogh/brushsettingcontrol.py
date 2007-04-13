# brushsettingcontrol.py
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
from goghutil import *


class BrushSettingControl:
    def __init__(self, parent, bound_attribute, label_text, min_value, max_value, digits):
        self.parent = parent
        xml = gtk.glade.XML(get_abspath("glade/goghglade.glade"), root="brush_setting_control")
        xml.signal_autoconnect(self)  
        self.control = xml.get_widget("brush_setting_control")
        self.brush_name_label = xml.get_widget("brush_name_label")
        self.brush_name_label.set_text(label_text)
        self.brush_scale = xml.get_widget("brush_control_scale")
        self.brush_scale.set_adjustment(gtk.Adjustment(min_value, min_value, max_value))
        self.brush_scale.set_digits(digits)
        self.bound_attribute = bound_attribute
        self.brush_data = None
        
        
    def on_brush_control_scale_value_changed(self, widget, data=None):
        new_value = self.brush_scale.get_value()
        if self.brush_data:
            setattr(self.brush_data, self.bound_attribute, new_value)
        self.parent.brush_manager.brush_selection_observer.notify_all()
            
    def set_brush_data(self, brush_data):
        self.brush_data = brush_data
        self.brush_scale.set_value(getattr(brush_data, self.bound_attribute))
        
