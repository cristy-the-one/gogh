# goghmain.py
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
import math
import time
import gnome.ui
import cPickle as pickle
from Numeric import *

from goghdoc import GoghDoc
from goghview import GoghView
from brushmanager import BrushManager
from brushstroke import BrushStroke
from layersdialog import LayersDialog
from resizedialog import ResizeDialog
from scaledialog import ScaleDialog
from savedialog import SaveDialog
from colordialog import ColorDialog
from brushmanagementdialog import BrushManagementDialog
from goghutil import *
from command import *


APPNAME='Gogh'
APPVERSION='0.0.1.060813'

def enable_devices():
    for device in gtk.gdk.devices_list():
        device.set_mode(gtk.gdk.MODE_SCREEN)
               
def get_pressure(event_data):
    for x in event_data.device.axes :
        if(x[0] == gtk.gdk.AXIS_PRESSURE) :
            pressure = event_data.get_axis(gtk.gdk.AXIS_PRESSURE)
            if not pressure :
                return 0
            return pressure
    return 1   
    
open_dialog_buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK)  
   
                     
class GoghWindow:

    def get_color_at(self, x, y):
        image = self.drawable.get_image(int(x), int(y), 1, 1)
        colormap = image.get_colormap()
        return colormap.query_color(image.get_pixel(0, 0))

    def on_gogh_drawing_window_destroy(self, widget, data=None):
        self.save_settings()
        gtk.main_quit()
        
    def on_color_select_button_clicked(self, widget, data=None):
        self.color_select_dialog.show()
           
    def on_brush_list_menubutton_clicked(self, widget, data=None):
        self.brush_management_dialog.show()
        
    def on_layers_button_clicked(self, widget, data=None):
        self.layers_dialog.show()
        
    def save_settings(self):
        try:
            self.brush_manager.save_brush_list()
        except:
            print 'Could not save the settings'            
               
        
    def on_eventbox_motion_notify_event(self, widget, data=None):
        if self.is_pressed :
            x, y = data.get_coords()
            x, y = self.goghview.to_model(x, y)
            self.brush_stroke.draw_to(x, y, get_pressure(data))
        if data.device.source==gtk.gdk.SOURCE_ERASER:
            self.brush_manager.select_eraser()
        else:
            self.brush_manager.unselect_eraser()
        
    def on_eventbox_button_press_event(self, widget, data=None):
        x, y = data.get_coords()
        if data.state & gtk.gdk.SHIFT_MASK:
            color = self.get_color_at(x, y)
            self.color_select_dialog.colorsel.set_current_color(color)
        else :
            x, y = self.goghview.to_model(x, y)
            color = self.color_select_dialog.colorsel.get_current_color()
            self.brush_stroke = BrushStroke(self.goghview, self.layers_dialog.selected_layer_key, color, self.brush_manager.active_brush_data)
            if data.device.source==gtk.gdk.SOURCE_ERASER:
                self.brush_stroke.is_erazer= True
            self.saved_pixbuf = self.get_selected_layer_pixbuf().copy()
            self.brush_stroke.start_draw(x, y) 
            self.is_pressed = True
        
    def on_eventbox_button_release_event(self, widget, data=None):
        if self.is_pressed :
            x, y = data.get_coords()
            x, y = self.goghview.to_model(x, y)
            self.brush_stroke.draw_to(x, y, 0) 
            self.is_pressed = False
            edit_action = EditLayerAction(self.goghdoc, self.layers_dialog.selected_layer_key, self.saved_pixbuf, self.brush_stroke.bounding_rectangle)
            self.goghdoc.command_stack.add(edit_action)
            self.goghdoc.pixbuf_observer.notify_all(self.brush_stroke.bounding_rectangle)

            
           
    def on_drawing_area_expose_event(self, widget, data=None):    
        area = data.area    
        #self.drawable.draw_pixbuf(self.drawable.new_gc(), self.goghview.pixbuf0, area.x, area.y, area.x, area.y, area.width, area.height)
        x = int(self.drawarea_scrolled_window.get_hadjustment().get_value())
        y = int(self.drawarea_scrolled_window.get_vadjustment().get_value())
        w = int(self.drawarea_scrolled_window.get_hadjustment().page_size)
        h = int(self.drawarea_scrolled_window.get_vadjustment().page_size)
        #print area.x, area.y, area.width, area.height
        self.reposition_view()
        self.goghview.reset_view_pixbuf()
        self.drawable.draw_pixbuf(self.drawable.new_gc(), self.goghview.pixbuf0, 0, 0, x, y, -1, -1)
        
       
    def on_undo1_activate(self, widget, data=None): 
        self.goghdoc.command_stack.undo()
        
    def on_redo1_activate(self, widget, data=None): 
        self.goghdoc.command_stack.redo()
        
    def on_resize1_activate(self, widget, data=None): 
        self.resize_dialog.show()
       
    def on_scale1_activate(self, widget, data=None): 
        self.scale_dialog.show()
        
        
    def on_quit1_activate(self, widget, data=None): 
        gtk.main_quit()
        
    def on_zoom_out_button_clicked(self, widget, data=None): 
        self.goghview.zoom_out()
        self.reset_cursor()
        
    def on_zoom_in_button_clicked(self, widget, data=None): 
        self.goghview.zoom_in()
        self.reset_cursor()
        
    def on_new1_activate(self, widget, data=None): 
        xml = gtk.glade.XML(get_abspath("glade/goghglade.glade"), root="new_document_dialog")
        new_dialog = xml.get_widget("new_document_dialog")
        response = new_dialog.run()
        width = xml.get_widget("width_spin").get_value_as_int()
        height = xml.get_widget("height_spin").get_value_as_int()
        if response in (gtk.RESPONSE_CANCEL, gtk.RESPONSE_DELETE_EVENT) :
            new_dialog.destroy()
            return
        width = xml.get_widget("width_spin").get_value_as_int()
        height = xml.get_widget("height_spin").get_value_as_int()
        new_dialog.destroy()
        goghdoc = GoghDoc(width = width, height = height)
        self.load_document(goghdoc)
        self.goghdoc.add_new_layer()
        
        
    def on_open1_activate(self, widget, data=None): 
        open_dialog = gtk.FileChooserDialog("Open", self.editor_window, gtk.FILE_CHOOSER_ACTION_OPEN, open_dialog_buttons)
        open_dialog.add_filter(self.gogh_filter)
        open_dialog.add_filter(self.image_file_filter)
        #open_dialog.add_filter(self.all_files_filter)
        response = open_dialog.run()
        if response in (gtk.RESPONSE_CANCEL, gtk.RESPONSE_DELETE_EVENT):
            open_dialog.destroy()
            return
        filename = open_dialog.get_filename()
        if open_dialog.get_filter()==self.gogh_filter :
            f = open(filename, "rb")
            goghdoc = pickle.load(f)
            f.close()
            self.load_document(goghdoc)
            self.current_filename = filename
        if open_dialog.get_filter()==self.image_file_filter:
            goghdoc = GoghDoc(pixbuf = gtk.gdk.pixbuf_new_from_file(filename))
            self.load_document(goghdoc)
        open_dialog.destroy()
        
    def on_save1_activate(self, widget, data=None): 
        if not self.goghdoc.has_name() :
            self.launch_save_dialog("Save")
        else:
            self.goghdoc.save(self.goghdoc.document_name)
        self.reset_window_title()
        
    def on_save_as1_activate(self, widget, data=None): 
        self.launch_save_dialog("Save As")      
        self.reset_window_title()
       
        
    def launch_save_dialog(self, dialog_title):     
        save_dialog = SaveDialog(self.goghdoc)      
        save_dialog.show()
           
       
    def on_gogh_drawing_window_key_press_event(self, widget, data=None): 
        if data.keyval==0xFFE1 :
            self.drawable.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND1))
        
    def on_gogh_drawing_window_key_release_event(self, widget, data=None): 
        if data.keyval==0xFFE1 :
            self.reset_cursor()

       
    def invalidate_drawing_area(self, rect) :
        self.drawable.invalidate_rect(rect, False) 
        
    def get_selected_layer_pixbuf(self):
        return self.goghdoc.layer_for_key(self.layers_dialog.selected_layer_key).pixbuf
        
    def resize_draw_area(self):
        w, h = self.goghview.get_size()
        self.draw_area.set_size_request(w, h)
        self.drawable.invalidate_rect(None, False) 
         #self.reposition_view()
        
    def reset_window_title(self):
        caption = "Gogh - "+self.goghdoc.document_name
        if self.goghdoc.is_changed_since_save():
            caption += " *"
        self.editor_window.set_title(caption)

    def load_document(self, goghdoc):        
        self.goghdoc = goghdoc
        self.goghdoc.reset_composite()
        self.goghview = GoghView(self.goghdoc, self.drawable)
        self.reset_cursor()
        self.resize_draw_area()
        self.goghdoc.command_stack.observer.add_callback(self.reset_window_title)
        self.goghview.image_observer.add_callback(self.layers_dialog.reset_images)
        self.goghview.image_observer.add_callback(self.invalidate_drawing_area)
        self.goghview.size_observer.add_callback(self.resize_draw_area)
        self.goghview.size_observer.add_callback(self.layers_dialog.reset_images)
        self.layers_dialog.set_document(self.goghdoc)
        self.resize_dialog.set_document(self.goghdoc)
        self.scale_dialog.set_document(self.goghdoc)
        self.reset_window_title()
        #self.reposition_view()

    #def drawarea_scrolled_window_hscrollbar_change_value(self, widget, scroll, value, data = None):
    #    self.reposition_view()
       
         
    #def drawarea_scrolled_window_vscrollbar_change_value(self, widget, scroll, value, data = None):
    #    self.reposition_view()
            
            
    def reposition_view(self):
        x = self.drawarea_scrolled_window.get_hadjustment().get_value()
        y = self.drawarea_scrolled_window.get_vadjustment().get_value()
        w = self.drawarea_scrolled_window.get_hadjustment().page_size
        h = self.drawarea_scrolled_window.get_vadjustment().page_size
        if self.goghview:
            self.goghview.reposition(x, y, w, h)
        
      

    def __init__(self):
        gnome.init(APPNAME, APPVERSION)   
        
        enable_devices()
        xml = gtk.glade.XML(get_abspath("glade/goghglade.glade"), root="gogh_drawing_window")
        xml.signal_autoconnect(self)    
        
       
        self.draw_area = xml.get_widget("drawing_area")
        self.drawable = self.draw_area.window
        self.drawarea_viewport = xml.get_widget("drawarea_viewport")
        self.editor_window = xml.get_widget("gogh_drawing_window")

        self.drawarea_scrolled_window = xml.get_widget("drawarea_scrolled_window")
        #print self.drawarea_scrolled_window
        #hscrollbar = self.drawarea_scrolled_window.get_hscrollbar()
        #vscrollbar = self.drawarea_scrolled_window.get_vscrollbar()
        #hscrollbar.connect("change-value", self.drawarea_scrolled_window_hscrollbar_change_value)
        #vscrollbar.connect("change-value", self.drawarea_scrolled_window_vscrollbar_change_value)
        
       
        self.brush_manager = BrushManager()
        
        self.layers_dialog = LayersDialog()
        self.layers_dialog.assign_check_menu_item(xml.get_widget("show_layer_selection1"))
        self.layers_dialog.dialog.add_accel_group(gtk.accel_groups_from_object(self.editor_window)[0])
        
        self.resize_dialog = ResizeDialog()
        self.scale_dialog = ScaleDialog()
            
        goghdoc = GoghDoc(width = 400, height = 400)
        goghdoc.add_new_layer()
        goghdoc.command_stack.clear()
        self.load_document(goghdoc)
            

        self.brush_list_button = xml.get_widget("brush_list_menubutton")
        self.brush_list_button.set_menu(self.brush_manager.brush_menu)
              

        self.color_select_dialog = ColorDialog() 
        self.color_select_dialog.assign_check_menu_item(xml.get_widget("show_color_selection1"))
        
        self.brush_manager.brush_selection_observer.add_callback(self.reset_cursor)
        
        self.brush_management_dialog = BrushManagementDialog(self.brush_manager)
        self.brush_management_dialog.assign_check_menu_item(xml.get_widget("show_brush_management_dialog1"))
        
        self.is_pressed = False
        self.reset_cursor()
        
        self.gogh_filter = gtk.FileFilter()
        self.gogh_filter.set_name("Gogh Documents")
        self.gogh_filter.add_pattern("*.gogh")
        self.gogh_filter.add_pattern("image/gogh")
        
        self.image_file_filter = gtk.FileFilter()
        self.image_file_filter.set_name("Images")
        self.image_file_filter.add_pattern("*.jpeg")
        self.image_file_filter.add_pattern("*.jpg")
        self.image_file_filter.add_pattern("*.png")
        self.image_file_filter.add_pattern("*.JPEG")
        self.image_file_filter.add_pattern("*.JPG")
        self.image_file_filter.add_pattern("*.PNG")
        self.image_file_filter.add_pattern("image/jpeg")
        self.image_file_filter.add_pattern("image/png")
        
        self.all_files_filter = gtk.FileFilter()
        self.all_files_filter.set_name("All files")
        self.all_files_filter.add_pattern("*")
        
        
    def reset_cursor(self):
        brush_data = self.brush_manager.active_brush_data
        w1, w2 = map(lambda(w): int(round(w*self.goghview.zoom_factor)) | 1, [brush_data.min_width, brush_data.max_width])
        d = max(w1, w2)
        pm = gtk.gdk.Pixmap(None, d+1, d+1,1)
        colormap = gtk.gdk.colormap_get_system()
        black = colormap.alloc_color('black')
        white = colormap.alloc_color('white')
        bgc = pm.new_gc(foreground=black)
        wgc = pm.new_gc(foreground=white)
        
        pm.draw_rectangle(bgc,True,0,0,d+1,d+1)
        
        pm.draw_arc(wgc,False, (d-w1)//2, (d-w1)//2, w1, w1, 0, 360*64)
        pm.draw_arc(wgc,False, (d-w2)//2, (d-w2)//2, w2, w2, 0, 360*64)
        
        self.drawable.set_cursor(gtk.gdk.Cursor(pm,pm,gtk.gdk.color_parse('black'), gtk.gdk.color_parse('white'),d//2,d//2))
       
    def main(self):
        gtk.main()

