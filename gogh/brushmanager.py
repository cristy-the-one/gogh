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
import xml.dom.minidom

from brushdata import BrushData, BrushType
from observer import Observer

from goghutil import *
from settingmanager import *

class BrushGroup:
    def __init__(self, name):
        self.brushes = []
        self.name = name
        

class BrushManager:
    def __init__(self):
        self.brush_types = {'pen': BrushType.Pen, 'eraser': BrushType.Eraser, 'smudge': BrushType.Smudge}
        self.brush_type_names = inverse_dictionary(self.brush_types)
        self.init_brush_list()
        self.current_pen_data = self.default_pen_data
        self.current_eraser_data = self.default_eraser_data
        self.active_brush_data = self.current_pen_data
        self.init_brush_menu()
        self.select_menu_item_for_active_brush_data()
        self.eraser_mode = False
        self.brush_selection_observer = Observer()
        
    def construct_brush_from_node(self, brush_node):
        brush = BrushData(brush_node.getAttribute("name"))
        for child_node in brush_node.childNodes:
            if child_node.localName=='width':
                brush.min_width = int(child_node.getAttribute("min"))
                brush.max_width = int(child_node.getAttribute("max"))
            if child_node.localName=='opacity':
                brush.min_opacity = float(child_node.getAttribute("min"))
                brush.max_opacity = float(child_node.getAttribute("max"))                    
            if child_node.localName=='step':
                brush.step = int(child_node.getAttribute("value"))
            if child_node.localName=='type':
                brush.brush_type = self.brush_types[child_node.childNodes[0].nodeValue]
            if child_node.localName=='default-eraser':
                self.default_eraser_data = brush
            if child_node.localName=='default-pen':
                self.default_pen_data = brush
        brush.populate_originals()
        return brush        
            
    def construct_node_from_brush(self, brush, xmldoc):
        brush_node = xmldoc.createElement('brush')
        brush_node.setAttribute('name', brush.name)
        brush_node.appendChild(xmldoc.createElement('width'))
        brush_node.lastChild.setAttribute('min', str(int(brush.min_width)))
        brush_node.lastChild.setAttribute('max', str(int(brush.max_width)))
        if brush.min_opacity!=0 or brush.max_opacity!=1:
            brush_node.appendChild(xmldoc.createElement('opacity'))
            brush_node.lastChild.setAttribute('min', str(brush.min_opacity))
            brush_node.lastChild.setAttribute('max', str(brush.max_opacity))
        if brush.step != 1:
            brush_node.appendChild(xmldoc.createElement('step'))
            brush_node.lastChild.setAttribute('value', str(int(brush.step)))
        brush_node.appendChild(xmldoc.createElement('type'))
        brush_node.lastChild.appendChild(xmldoc.createTextNode(self.brush_type_names[brush.brush_type]))
        if self.default_pen_data == brush :
            brush_node.appendChild(xmldoc.createElement('default-pen'))
        if self.default_eraser_data == brush :
            brush_node.appendChild(xmldoc.createElement('default-eraser'))
        return brush_node        
                
    def init_brush_list(self):
        original_doc, custom_doc = load_original_brush_list_xmldoc(), load_custom_brush_list_xmldoc()
        self.brush_groups = []
        self.load_brushes_from_document(original_doc, True)
        if custom_doc:
            self.load_brushes_from_document(custom_doc, False)
                    
    def load_brushes_from_document(self, doc, is_original):
        for group_node in doc.getElementsByTagName("brushgroup"):
            group_name = group_node.getAttribute("name")
            group = find_item(self.brush_groups, lambda g : g.name == group_name)
            if not group:
                group = BrushGroup(group_node.getAttribute("name"))
                self.brush_groups.append(group)        
            for brush_node in group_node.getElementsByTagName("brush"):
                brush = self.construct_brush_from_node(brush_node)
                brush.is_original = is_original
                group.brushes.append(brush)
       
            
    def save_brush_list(self):
        doc = xml.dom.minidom.Document()
        root_node = doc.createElement('brushes')
        doc.appendChild(root_node)
        for group in self.brush_groups:
            group_node = doc.createElement('brushgroup')
            group_node.setAttribute('name', group.name)
            for brush in group.brushes:
                if not brush.is_original:
                    brush_node = self.construct_node_from_brush(brush, doc)
                    group_node.appendChild(brush_node)
            root_node.appendChild(group_node)
        save_brush_list_xmldoc(doc)
        
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
        
    def select_brush(self, brush_data):
        if self.active_brush_data!=brush_data :
            self.active_brush_data = brush_data
            self.brush_selection_observer.notify_all()
            self.assign_current_brushes()
            self.select_menu_item_for_active_brush_data()
        
       
      
           
        
        
    

        
