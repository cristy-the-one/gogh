# command.py
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

import cPickle as pickle
import zlib

from goghutil import *
from observer import Observer

max_stack_len = 100

class CommandStack:
    def __init__(self, goghdoc):
        self.packed_command_list = []
        self.current_index = -1;
        self.goghdoc = goghdoc
        self.observer = Observer()
        self.changes_since_save = 0

    def add(self, command):
        if(command.is_trivial()):
            return
        del self.packed_command_list[self.current_index+1:]
        self.packed_command_list.append(self.pack_command(command))
        self.current_index+=1
        self.changes_since_save+=1
        command.execute()
        if len(self.packed_command_list)>max_stack_len:
            self.current_index -= len(self.packed_command_list)-max_stack_len
            del self.packed_command_list[:-max_stack_len]
        self.observer.notify_all()

    def undo(self):
        if self.current_index<0:
            return
        command = self.unpack_command(self.packed_command_list[self.current_index])
        command.undo()
        self.current_index-=1
        self.changes_since_save-=1
        self.observer.notify_all()

    def redo(self):
        if self.current_index+1>=len(self.packed_command_list):
            return
        command = self.unpack_command(self.packed_command_list[self.current_index+1])
        command.redo()
        self.current_index+=1
        self.changes_since_save+=1
        self.observer.notify_all()

    def pack_command(self, command):
        return zlib.compress(pickle.dumps(command, 2))

    def unpack_command(self, packed_command):
        command = pickle.loads(zlib.decompress(packed_command))
        command.goghdoc = self.goghdoc
        return command

    def clear(self):
        self.packed_command_list = []
        self.current_index = -1;



class Action:
    def execute(self):
        raise TypeError('Abstract method called')

    def undo(self):
        raise TypeError('Abstract method called')

    def redo(self):
        raise TypeError('Abstract method called')

    def is_trivial(self):
        return False

    def __getstate__(self):
        state = self.__dict__.copy()
        del state["goghdoc"]
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)


class EditLayerAction(Action):
    def __init__(self, goghdoc, layer_key, original_pixbuf, edit_area):
        self.trivial = False
        if(not edit_area):
            self.trivial = True
            return
        self.goghdoc = goghdoc
        self.layer_key = layer_key
        layer_pixbuf = self.goghdoc.layer_for_key(self.layer_key).pixbuf
        self.new_pixels = get_pixels_from_pixbuf(layer_pixbuf, edit_area).copy()
        self.old_pixels = get_pixels_from_pixbuf(original_pixbuf, edit_area).copy()
        self.edit_area = rect_to_list(edit_area)
        if(alltrue(alltrue(alltrue(self.new_pixels==self.old_pixels)))):
            self.trivial = True

    def execute(self):
        pass

    def undo(self):
        layer_pixbuf = self.goghdoc.layer_for_key(self.layer_key).pixbuf
        pixels = get_pixels_from_pixbuf(layer_pixbuf, rect_from_list(self.edit_area))
        pixels[:,:,:]=self.old_pixels[:,:,:]
        self.goghdoc.reset_composite()
        self.goghdoc.pixbuf_observer.notify_all(rect_from_list(self.edit_area))

    def redo(self):
        layer_pixbuf = self.goghdoc.layer_for_key(self.layer_key).pixbuf
        pixels = get_pixels_from_pixbuf(layer_pixbuf, rect_from_list(self.edit_area))
        pixels[:,:,:]=self.new_pixels[:,:,:]
        self.goghdoc.reset_composite()
        self.goghdoc.pixbuf_observer.notify_all(rect_from_list(self.edit_area))


    def is_trivial(self):
        return self.trivial



class InsertLayerAction(Action):
    def __init__(self, goghdoc, key, position):
        self.goghdoc = goghdoc
        self.layer_key = key
        self.layer_position = position

    def execute(self):
        new_layer = self.goghdoc.create_layer(self.layer_key)
        self.goghdoc.layers.insert(self.layer_position, new_layer)
        self.goghdoc.layer_list_observer.notify_all(self.layer_key)

    def undo(self):
        del self.goghdoc.layers[self.layer_position]
        self.goghdoc.layer_list_observer.notify_all(self.layer_key)

    def redo(self):
        self.execute()


class RemoveLayerAction(Action):
    def __init__(self, goghdoc, layer_key):
        self.goghdoc = goghdoc
        self.layer_key = layer_key
        self.layer_position = find_index(self.goghdoc.layers, lambda layer : layer.key == self.layer_key)
        self.layer = self.goghdoc.layers[self.layer_position]

    def execute(self):
        del self.goghdoc.layers[self.layer_position]
        self.goghdoc.reset_composite()
        self.goghdoc.layer_list_observer.notify_all()
        self.goghdoc.pixbuf_observer.notify_all()

    def undo(self):
        self.goghdoc.layers.insert(self.layer_position, self.layer)
        self.goghdoc.reset_composite()
        self.goghdoc.layer_list_observer.notify_all()
        self.goghdoc.pixbuf_observer.notify_all()

    def redo(self):
        self.execute()


class MoveLayerAction(Action):
    def __init__(self, goghdoc, layer_key, position):
        self.goghdoc = goghdoc
        self.layer_key = layer_key
        self.new_position = position
        self.old_position = find_index(self.goghdoc.layers, lambda layer : layer.key == self.layer_key)
        self.trivial = (self.new_position==self.old_position)

    def execute(self):
        swap_items(self.goghdoc.layers, self.new_position, self.old_position)
        self.goghdoc.reset_composite()
        self.goghdoc.pixbuf_observer.notify_all()
        self.goghdoc.layer_list_observer.notify_all()

    def undo(self):
        self.execute()

    def redo(self):
        self.execute()

class ChangeLayerOpacityAction(Action):
    def __init__(self, goghdoc, layer_key, new_alpha):
        self.goghdoc = goghdoc
        self.layer_key = layer_key
        self.new_alpha = new_alpha
        self.old_alpha = self.goghdoc.layer_for_key(self.layer_key).alpha
        self.trivial = (self.new_alpha==self.old_alpha)

    def execute(self):
        self.goghdoc.layer_for_key(self.layer_key).alpha = self.new_alpha
        self.goghdoc.reset_composite()
        self.goghdoc.pixbuf_observer.notify_all()

    def undo(self):
        self.goghdoc.layer_for_key(self.layer_key).alpha = self.old_alpha
        self.goghdoc.reset_composite()
        self.goghdoc.pixbuf_observer.notify_all()

    def redo(self):
        self.execute()

class RenameLayerAction(Action):
    def __init__(self, goghdoc, layer_key, new_name):
        self.goghdoc = goghdoc
        self.layer_key = layer_key
        self.new_name = new_name
        self.old_name = self.goghdoc.layer_for_key(self.layer_key).name
        self.trivial = (self.new_name==self.old_name)

    def execute(self):
        self.goghdoc.layer_for_key(self.layer_key).name = self.new_name
        self.goghdoc.pixbuf_observer.notify_all()

    def undo(self):
        self.goghdoc.layer_for_key(self.layer_key).name = self.old_name
        self.goghdoc.pixbuf_observer.notify_all()

    def redo(self):
        self.execute()


class ChangeLayerBlendModeAction(Action):
    def __init__(self, goghdoc, layer_key, new_blend_mode):
        self.goghdoc = goghdoc
        self.layer_key = layer_key
        self.new_blend_mode = new_blend_mode
        self.old_blend_mode = self.goghdoc.layer_for_key(self.layer_key).blend_mode
        self.trivial = (self.new_blend_mode==self.old_blend_mode)

    def execute(self):
        self.goghdoc.layer_for_key(self.layer_key).blend_mode = self.new_blend_mode
        self.goghdoc.reset_composite()
        self.goghdoc.pixbuf_observer.notify_all()

    def undo(self):
        self.goghdoc.layer_for_key(self.layer_key).blend_mode = self.old_blend_mode
        self.goghdoc.reset_composite()
        self.goghdoc.pixbuf_observer.notify_all()

    def redo(self):
        self.execute()

class ResizeAction(Action):
    def __init__(self, goghdoc, adjustments):
        self.left, self.top, self.right, self.bottom = adjustments
        self.leftN, self.topN, self.rightN, self.bottomN = map(lambda x: -min(x, 0), adjustments)
        self.goghdoc = goghdoc
        self.left_areas, self.top_areas, self.right_areas, self.bottom_areas = {}, {}, {}, {}
        for layer in self.goghdoc.layers:
            layer_pixels = layer.pixbuf.get_pixels_array()
            self.left_areas[layer.key] = layer_pixels[:, :self.leftN, :].copy()
            self.right_areas[layer.key] = layer_pixels[:, -self.rightN:, :].copy()
            middle_area=layer_pixels[:, self.leftN:self.goghdoc.width-self.rightN, :]
            self.top_areas[layer.key] = middle_area[:self.topN ,: ,:].copy()
            self.bottom_areas[layer.key] = middle_area[-self.bottomN: ,: ,:].copy()

    def execute(self):
        self.goghdoc.width+=self.left+self.right
        self.goghdoc.height+=self.top+self.bottom
        for layer in self.goghdoc.layers:
            new_pixbuf = create_pixbuf(self.goghdoc.width,self.goghdoc.height)
            new_pixbuf.fill(0xFFFFFF00)
            copy_onto(layer.pixbuf.get_pixels_array(), new_pixbuf.get_pixels_array(), self.left, self.top)
            layer.pixbuf = new_pixbuf
        self.recomposite_goghdoc()

    def undo(self):
        self.goghdoc.width-=self.left+self.right
        self.goghdoc.height-=self.top+self.bottom
        for layer in self.goghdoc.layers:
            new_pixbuf = create_pixbuf(self.goghdoc.width,self.goghdoc.height)
            new_pixbuf_pixels = new_pixbuf.get_pixels_array()
            copy_onto(layer.pixbuf.get_pixels_array(), new_pixbuf_pixels, -self.left, -self.top)
            copy_onto(self.left_areas[layer.key], new_pixbuf_pixels, 0, 0)
            copy_onto(self.right_areas[layer.key], new_pixbuf_pixels, self.goghdoc.width-self.rightN, 0)
            copy_onto(self.top_areas[layer.key], new_pixbuf_pixels, self.leftN, 0)
            copy_onto(self.bottom_areas[layer.key], new_pixbuf_pixels, self.leftN, self.goghdoc.height-self.bottomN)
            layer.pixbuf = new_pixbuf
        self.recomposite_goghdoc()

    def redo(self):
        self.execute()

    def recomposite_goghdoc(self):
        self.goghdoc.background = create_pixbuf(self.goghdoc.width,self.goghdoc.height)
        self.goghdoc.background.fill(0xFFFFFFFF)
        self.goghdoc.reset_composite()
        self.goghdoc.size_observer.notify_all()


class ScaleAction(Action):
    def __init__(self, goghdoc, width, height):
        self.goghdoc = goghdoc
        self.old_width, self.old_height = self.goghdoc.width, self.goghdoc.height
        self.new_width, self.new_height = width, height
        self.layer_pixbufs = {}
        for layer in self.goghdoc.layers :
            self.layer_pixbufs[layer.key] = layer.pixbuf.get_pixels_array()[...]

    def execute(self):
        for layer in self.goghdoc.layers:
            layer.pixbuf = layer.pixbuf.scale_simple(self.new_width, self.new_height, gtk.gdk.INTERP_HYPER)
        self.goghdoc.width, self.goghdoc.height = self.new_width, self.new_height
        self.recomposite_goghdoc()

    def undo(self):
        self.goghdoc.width, self.goghdoc.height = self.old_width, self.old_height
        for layer in self.goghdoc.layers :
            layer.pixbuf = create_pixbuf(self.goghdoc.width,self.goghdoc.height)
            pixels = layer.pixbuf.get_pixels_array()
            pixels[...] = self.layer_pixbufs[layer.key][...]
        self.recomposite_goghdoc()

    def redo(self):
        self.execute()

    def recomposite_goghdoc(self):
        self.goghdoc.background = create_pixbuf(self.goghdoc.width,self.goghdoc.height)
        self.goghdoc.background.fill(0xFFFFFFFF)
        self.goghdoc.reset_composite()
        self.goghdoc.size_observer.notify_all()




class ClearLayerAction(Action):
    def __init__(self, layer_pixbuf):
        pass



