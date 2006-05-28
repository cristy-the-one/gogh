# goghdoc.py
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
from goghutil import *
from command import *
from observer import Observer
import cPickle as pickle
    
class LayerBlendModes:
    Standard, Add, Subtract, Diff, Mult, Div, Screen, Overlay, Darken, Lighten = range(10)

class GoghLayer:
    def __init__(self, width, height, key):
        self.pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, width, height) 
        self.pixbuf.fill(0xFFFFFF00)
        self.alpha = 1.0
        self.key = key
        self.name = "Layer "+str(key)
        self.is_locked = False
        self.blend_mode = LayerBlendModes.Standard
        
    def __getstate__(self):
        state = self.__dict__.copy()
        del state["pixbuf"]
        state["png"] = PixbufSerializer().save_pixbuf(self.pixbuf)
        return state
        
    def __setstate__(self, state):
        pixels = state["png"]
        self.pixbuf = PixbufSerializer().load_pixbuf(state["png"])
        if "blend_mode" not in state:
            self.blend_mode = LayerBlendModes.Standard
        self.__dict__.update(state)

default_document_name = 'Untitled'

class GoghDoc:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.next_layer_key = 1
        self.layers = []
        self.background = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, self.width, self.height)  
        self.background.fill(0xFFFFFFFF)
        self.composite = self.background.copy()
        self.command_stack = CommandStack(self)
        self.document_name = default_document_name
        self.size_observer = Observer()  
        self.pixbuf_observer = Observer()  
        self.layer_list_observer = Observer()
            
    def has_name(self):
        return self.document_name != default_document_name    
    
        
    def __getstate__(self):
        state = self.__dict__.copy()
        del state["next_layer_key"]
        del state["background"]
        del state["composite"]
        del state["command_stack"]
        del state["size_observer"]
        del state["pixbuf_observer"]
        del state["layer_list_observer"]
        return state       
        
    def __setstate__(self, state):
        self.__dict__.update(state)
        self.background = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, self.width, self.height)  
        self.background.fill(0xFFFFFFFF)
        self.size_observer = Observer()  
        self.pixbuf_observer = Observer()  
        self.layer_list_observer = Observer()
        self.reset_composite()
        self.command_stack = CommandStack(self)
        self.next_layer_key = 1+max(map(lambda layer: layer.key, self.layers))
            
    def create_layer(self, key):
        return GoghLayer(self.width, self.height, key)
        
    def insert_new_layer(self, key, position):
        insert_layer_action = InsertLayerAction(self, key, position)
        self.command_stack.add(insert_layer_action)
        return self.layers[position]    
        
    def add_new_layer(self): 
        layer = self.insert_new_layer(self.next_layer_key, len(self.layers))
        self.next_layer_key += 1
        return layer
        
        
    def remove_layer(self, key):
        remove_layer_action = RemoveLayerAction(self, key)
        self.command_stack.add(remove_layer_action)

        
    def move_layer_down(self, key):
        index = find_index(self.layers, lambda layer: layer.key==key)
        if index > 0:
            move_layer_action = MoveLayerAction(self, key, index-1)
            self.command_stack.add(move_layer_action)
        
    def move_layer_up(self, key):
        index = find_index(self.layers, lambda layer: layer.key==key)
        if index < len(self.layers)-1:
            move_layer_action = MoveLayerAction(self, key, index+1)
            self.command_stack.add(move_layer_action)
     
    def combine_layers(self, x, y, w, h):
        self.background.copy_area(x, y, w, h, self.composite, x, y)        
        for layer in self.layers:   
            if layer.blend_mode==LayerBlendModes.Standard:
                alpha256 = int(round(255*layer.alpha))
                layer.pixbuf.composite(self.composite, x, y, w, h, 0, 0, 1, 1, gtk.gdk.INTERP_NEAREST, alpha256)
            else:
                self.blend_areas(self.composite.get_pixels_array()[y:y+h,x:x+w], layer.pixbuf.get_pixels_array()[y:y+h,x:x+w], layer.blend_mode, layer.alpha)
                
                
    def blend_areas(self, dest, src, blend_mode, alpha):
        dest_rgb, dest_alpha = dest[:, :, 0:3], dest[:, :, 3]
        src_rgb, src_alpha = src[:, :, 0:3], src[:, :, 3]
        dest_alpha[:,:] = (255-(255-dest_alpha)*(255-src_alpha)/255).astype(UInt8)[:,:]
        alphas = (src[:, :, 3:]*alpha/255.0)[:,:,:]
        if blend_mode==LayerBlendModes.Add:
            result = minimum(255, dest_rgb+src_rgb*alphas)
        if blend_mode==LayerBlendModes.Subtract:
            result = maximum(0, dest_rgb-src_rgb*alphas)
        if blend_mode==LayerBlendModes.Diff:
            result = abs(dest_rgb-src_rgb*alphas)
        if blend_mode==LayerBlendModes.Mult:
            result = dest_rgb*(src_rgb/255.0)
            result = result*alphas+dest_rgb*(1-alphas)
        if blend_mode==LayerBlendModes.Div:
            result = dest_rgb/((src_rgb+1)/256.0)
            result = minimum(255, result*alphas+dest_rgb*(1-alphas))
        if blend_mode==LayerBlendModes.Darken:
            result = minimum(dest_rgb, src_rgb)
            result = result*alphas+dest_rgb*(1-alphas)
        if blend_mode==LayerBlendModes.Lighten:
            result = maximum(dest_rgb, src_rgb)  
            result = result*alphas+dest_rgb*(1-alphas)

        dest_rgb[:, :, :] = result.astype(UInt8)[:,:,:]

             
    def reset_composite(self):
        self.composite = self.background.copy()
        self.combine_layers(0, 0, self.width, self.height)
            
    def put_pixbuf_on_layer(self, pixbuf, x, y, alpha, layer_key):
        layer_pixbuf = self.layer_for_key(layer_key).pixbuf
        put_pixbuf_on_pixbuf(pixbuf, layer_pixbuf, x, y, alpha)  
        self.combine_layers(x, y, pixbuf.get_width(), pixbuf.get_height())
 
    def subtract_alpha(self, pixbuf, x, y, alpha, layer_key):
        layer_pixbuf = self.layer_for_key(layer_key).pixbuf
        subtract_alpha(pixbuf, layer_pixbuf, x, y, alpha)  
        self.combine_layers(x, y, pixbuf.get_width(), pixbuf.get_height())  
    
    def layer_for_key(self, key):
        return find_item(self.layers, lambda layer: layer.key==key)
        
    def save(self, filename):
        f = open(filename, "wb")
        pickle.dump(self, f, 2)
        f.close()
        self.command_stack.changes_since_save=0
        
    def is_changed_since_save(self):
        return not self.has_name() or self.command_stack.changes_since_save!=0
        

        

