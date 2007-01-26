# layersdialog.py
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
from command import ChangeLayerOpacityAction, ChangeLayerBlendModeAction
from goghtooldialog import GoghToolDialog
from goghutil import *
from goghdoc import LayerBlendModes

class LayerControl:
    def __init__(self, parent, layer):
        self.parent = parent
        self.goghdoc = self.parent.goghdoc
        self.layer = layer
        xml = gtk.glade.XML(get_abspath("glade/goghglade.glade"), root="layer_control")
        xml.signal_autoconnect(self)  
        self.control = xml.get_widget("layer_control")
        self.layer_name_label = xml.get_widget("layer_name_label")
        self.opacity_scale = xml.get_widget("opacity_scale")
        self.thumbnail_area = xml.get_widget("thumbnail_drawing_area")
        self.blend_mode_combobox = xml.get_widget("blend_mode_combobox")
        self.layer_name_label.set_text(self.layer.name)
        self.opacity_scale.set_value(self.layer.alpha)
        
        self.liststore = gtk.ListStore(object, str)
        self.liststore.append([LayerBlendModes.Standard, "Standard"])
        self.liststore.append([LayerBlendModes.Darken, "Darken"])
        self.liststore.append([LayerBlendModes.Lighten, "Lighten"])
        self.liststore.append([LayerBlendModes.Add, "Addition"])
        self.liststore.append([LayerBlendModes.Subtract, "Subtraction"])
        self.liststore.append([LayerBlendModes.Diff, "Difference"])
        self.liststore.append([LayerBlendModes.Mult, "Multiply"])
        self.liststore.append([LayerBlendModes.Div, "Divide"])
        self.blend_mode_combobox.set_model(self.liststore)
        combo_cell = gtk.CellRendererText()
        self.blend_mode_combobox.pack_start(combo_cell, True)
        self.blend_mode_combobox.add_attribute(combo_cell, 'text', 1)
        self.blend_mode_combobox.set_active(find_item(self.liststore, lambda(row): row[0]==self.layer.blend_mode).path[0])
        
    def on_thumbnail_drawing_area_expose_event(self, widget, data=None):
        drawable = self.thumbnail_area.window
        area_w, area_h = drawable.get_size()
        k = min(area_w/self.goghdoc.width, area_h/self.goghdoc.height)
        w, h = int(self.goghdoc.width*k), int(self.goghdoc.height*k)
        x0, y0 = (area_w-w)//2, (area_h-h)//2
        scaled_pixbuf = self.layer.pixbuf.scale_simple(w, h, gtk.gdk.INTERP_BILINEAR)
        gc = drawable.new_gc()
        drawable.draw_pixbuf(gc, scaled_pixbuf, 0, 0, x0, y0)
        if self.layer.key==self.parent.selected_layer_key:
            drawable.draw_rectangle(gc, False, x0, y0, area_w-x0-1, area_h-y0-1)
        
    def on_thumbnail_eventbox_button_release_event(self, widget, data=None):
        self.parent.select_layer(self.layer.key)
        
    def on_opacity_scale_value_changed(self, widget, data=None):
        new_alpha = self.opacity_scale.get_value()
        if self.layer.alpha == new_alpha:
            return
        change_opacity_action = ChangeLayerOpacityAction(self.goghdoc, self.layer.key, new_alpha)
        self.goghdoc.command_stack.add(change_opacity_action)   
        
    def on_blend_mode_combobox_changed(self, widget, data=None):        
        new_blend_mode = self.liststore[self.blend_mode_combobox.get_active()][0]
        if new_blend_mode==self.layer.blend_mode:
            return
        change_layer_blend_mode_action = ChangeLayerBlendModeAction(self.goghdoc, self.layer.key, new_blend_mode)
        self.goghdoc.command_stack.add(change_layer_blend_mode_action)   

        
    def reset(self):
        self.thumbnail_area.window.invalidate_rect(None, False) 
        self.opacity_scale.set_value(self.layer.alpha)
        self.blend_mode_combobox.set_active(find_item(self.liststore, lambda(row): row[0]==self.layer.blend_mode).path[0])
       
       

class LayersDialog(GoghToolDialog):
    def __init__(self):
        xml = gtk.glade.XML(get_abspath("glade/goghglade.glade"), root="layers_window")
        xml.signal_autoconnect(self)  
        self.dialog = xml.get_widget("layers_window")
        self.vbox = xml.get_widget("layers_vbox")
        self.layer_controls = []
        
    def set_document(self, goghdoc):
        self.goghdoc = goghdoc
        self.selected_layer_key = None
        self.reset_layer_controls()  
        self.goghdoc.layer_list_observer.add_callback(self.reset_layer_controls)
        
    def repopulate_control_list(self):
        new_layer_controls_list = []
        for child_control in self.vbox.get_children():
            self.vbox.remove(child_control)
        for layer in self.goghdoc.layers:
            layer_control = find_item(self.layer_controls, lambda c : c.layer==layer)
            if not layer_control:
                layer_control = LayerControl(self, layer)
            new_layer_controls_list.append(layer_control)
            self.vbox.pack_end(layer_control.control, False, False)    
        self.layer_controls = new_layer_controls_list
    
        
    def reset_layer_controls(self, sel_key = None):
        self.repopulate_control_list()
        if not sel_key:
            sel_key = self.selected_layer_key
        if sel_key and find_item(self.goghdoc.layers, lambda layer : layer.key==sel_key):
            self.selected_layer_key = sel_key
        else:
            if len(self.goghdoc.layers)>0 :
                self.selected_layer_key = self.goghdoc.layers[-1].key
            else:
                self.selected_layer_key = None
            
                       
    def reset_images(self, rect=None) :
        if not self.dialog.get_property('visible'):
            return
        for layer_control in self.layer_controls:
            layer_control.reset()
            
    def on_layers_window_visibility_notify_event(self, widget, data=None):
        self.reset_images()
            
    def select_layer(self, layer_key):
        self.selected_layer_key = layer_key
        for layer_control in self.layer_controls:
            layer_control.selected = (layer_control.layer.key==layer_key)
            layer_control.thumbnail_area.window.invalidate_rect(None, False) 
            
    def on_add_layer_button_clicked(self, widget, data=None): 
        self.goghdoc.add_new_layer()
        
    def on_remove_layer_button_clicked(self, widget, data=None): 
        self.goghdoc.remove_layer(self.selected_layer_key)
        
    def on_move_layer_up_button_clicked(self, widget, data=None): 
        self.goghdoc.move_layer_up(self.selected_layer_key)
        
    def on_move_layer_down_button_clicked(self, widget, data=None): 
        self.goghdoc.move_layer_down(self.selected_layer_key)
        
    def on_layers_window_delete_event(self, widget, data=None):
        self.hide()
        return True
