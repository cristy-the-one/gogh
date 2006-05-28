# brushmanager.py
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

from brushdata import BrushData, BrushType
from observer import Observer

from goghutil import *

class BrushGroup:
    def __init__(self, name):
        self.brushes = []
        self.name = name
        

class BrushManager:
    def __init__(self):
        self.init_brush_list()
        self.active_brush_data = self.brush_groups[0].brushes[0]
        self.current_eraser_data = find_item(self.eraser_group.brushes, lambda b : b.brush_type == BrushType.Eraser)
        self.current_pen_data = self.active_brush_data
        self.init_brush_menu()
        self.select_menu_item_for_active_brush_data()
        self.eraser_mode = False
        self.brush_selection_observer = Observer()
        
        
    def init_brush_list(self):
        self.brush_groups = []
        self.brush_groups.append(BrushGroup("Brushes"))
        self.brush_groups[-1].brushes.append(BrushData(name="Pencil"))
        self.brush_groups[-1].brushes.append(BrushData(name="Wide", min_width=20, max_width=25, step = 3))
        self.eraser_group = BrushGroup("Erasers")
        self.brush_groups.append(self.eraser_group)
        self.brush_groups[-1].brushes.append(BrushData(name="Eraser", brush_type=BrushType.Eraser, min_width=5, max_width=8))
        
    def init_brush_menu(self):
        self.brush_menu = gtk.Menu()
        self.brush_menu.connect("selection-done", self.selection_done)
        self.items_for_brushes = {}
        self.menu_item_group = None
        for brush_group in self.brush_groups:
            for brush_data in brush_group.brushes:
                item = gtk.RadioMenuItem(self.menu_item_group, brush_data.name)
                self.items_for_brushes[brush_data] = item
                if not self.menu_item_group:
                    self.menu_item_group = item
                self.brush_menu.append(item)
        self.brush_menu.append(gtk.SeparatorMenuItem())
        self.brush_menu.show_all()
        
    def selection_done(self, widget, data=None): 
        for brush_data, item in self.items_for_brushes.iteritems():
            if item.get_active():
                self.active_brush_data = brush_data
                self.brush_selection_observer.notify_all()
                self.assign_current_brushes()
                self.select_menu_item_for_active_brush_data()
                return
        
    def select_eraser(self):
        self.eraser_mode = True
        if self.active_brush_data!=self.current_eraser_data :
            self.current_pen_data = self.active_brush_data
            self.active_brush_data = self.current_eraser_data
            self.brush_selection_observer.notify_all()
            self.select_menu_item_for_active_brush_data()

         
    def unselect_eraser(self):
        self.eraser_mode = False
        if self.active_brush_data!=self.current_pen_data :
            self.current_eraser_data = self.active_brush_data
            self.active_brush_data = self.current_pen_data
            self.brush_selection_observer.notify_all()
            self.select_menu_item_for_active_brush_data()
            
    def select_menu_item_for_active_brush_data(self):
        item = self.items_for_brushes[self.active_brush_data]
        self.brush_menu.select_item(item)
        item.set_active(True)
        
    def assign_current_brushes(self):
        if self.eraser_mode :
            self.current_eraser_data = self.active_brush_data
        else :
            self.current_pen_data = self.active_brush_data
        
        
    def on_brush_name_changed(self, brush_data) :
        self.items_for_brushes[brush_data].child.set_text(brush_data.name)
        
    def group_for_brush(self, brush_data):
        return find_item(self.brush_groups, lambda g : brush_data in g.brushes)
        
    def add_brush(self, brush_group, brush_data):
        brush_group.brushes.append(brush_data)
        new_item = gtk.RadioMenuItem(self.menu_item_group, brush_data.name)
        self.items_for_brushes[brush_data] = new_item
        self.brush_menu.append(new_item)
        self.brush_menu.show_all()
        
    def remove_brush(self, brush_data):
        brush_group = self.group_for_brush(brush_data)
        brush_group.brushes.remove(brush_data)
        self.brush_menu.remove(self.items_for_brushes[brush_data])
        del self.items_for_brushes[brush_data]
        self.brush_menu.show_all()
       
      
           
        
        
    

        
