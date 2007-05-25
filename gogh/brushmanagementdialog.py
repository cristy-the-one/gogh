# brushmanagementdialog.py
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

import gtk
import gtk.gdk
import gtk.glade
import gobject
import pango
from goghtooldialog import GoghToolDialog
from brushmanager import BrushManager
from brushdata import BrushData, BrushType
from brushsettingcontrol import BrushSettingControl
from goghutil import *


class BrushManagementDialog(GoghToolDialog):
    def __init__(self, brush_manager):
        self.brush_manager = brush_manager

        xml = gtk.glade.XML(get_abspath("glade/goghglade.glade"), root="brush_management_form")
        xml.signal_autoconnect(self)
        self.dialog = xml.get_widget("brush_management_form")
        self.treeview = xml.get_widget("brush_list_treeview")
        self.brush_group_controls = xml.get_widget("brush_group_hbox")
        self.brush_settings_controls = xml.get_widget("brush_settings_vbox")
        self.restore_brush_settings_button = xml.get_widget("restore_brush_settings_button")
        self.brush_group_name_label = xml.get_widget("brush_group_name_label")

        self.brush_type_combobox = xml.get_widget("brush_type_combobox")

        self.left_vbox = xml.get_widget("left_vbox")
        self.right_vbox = xml.get_widget("right_vbox")

        xml_menu = gtk.glade.XML(get_abspath("glade/goghglade.glade"), root="brush_list_menu")
        xml_menu.signal_autoconnect(self)
        self.brush_list_menu = xml_menu.get_widget("brush_list_menu")
        self.delete_brush_menu_item = xml_menu.get_widget("delete_brush_menu_item")
        self.rename_brush_menu_item = xml_menu.get_widget("rename_brush_menu_item")

        self.setup_treestore()
        self.setup_treeview()

        self.liststore = gtk.ListStore(object, str)
        self.liststore.append([BrushType.Pen, "Pen"])
        self.liststore.append([BrushType.Eraser, "Eraser"])
        self.liststore.append([BrushType.Smudge, "Smudge"])
        self.brush_type_combobox.set_model(self.liststore)
        combo_cell = gtk.CellRendererText()
        self.brush_type_combobox.pack_start(combo_cell, True)
        self.brush_type_combobox.add_attribute(combo_cell, 'text', 1)
        self.brush_controls = []

        self.brush_manager.brush_selection_observer.add_callback(self.change_selected_brush)


    def show(self):
        self.create_controls_for_brush_type(self.brush_manager.active_brush_data.brush_type)
        GoghToolDialog.show(self)
        self.set_selected_brush(self.brush_manager.active_brush_data)

    def remove_all_brush_control(self):
        for child_control in self.left_vbox.get_children():
            self.left_vbox.remove(child_control)
        for child_control in self.right_vbox.get_children():
            self.right_vbox.remove(child_control)

    def set_brush_data_for_all_brush_controls(self, brush_data):
        for brush_control in self.brush_controls:
            brush_control.set_brush_data(brush_data)

    def change_selected_brush(self):
        self.set_selected_brush(self.brush_manager.active_brush_data)

    def set_selected_brush(self, brush_data):
        row = self.get_row_for_brush(brush_data)
        if row:
            self.treeview.expand_to_path(row.path)
            self.treeview.set_cursor(row.path, self.treeview.get_column(0))


    def create_controls_for_brush_type(self, brush_type):
        self.remove_all_brush_control()
        min_size_control = BrushSettingControl(self, 'min_width', 'Brush size at lowest pressure', 1, 30, 0)
        max_size_control = BrushSettingControl(self, 'max_width', 'Brush size at highest pressure', 1, 30, 0)
        self.brush_controls = [min_size_control, max_size_control]

        self.left_vbox.pack_start(min_size_control.control, False, False)
        self.right_vbox.pack_start(max_size_control.control, False, False)

        if brush_type!=BrushType.Smudge:
            min_opacity_control = BrushSettingControl(self, 'min_opacity', 'Opacity at lowest pressure', 0, 1, 2)
            max_opacity_control = BrushSettingControl(self, 'max_opacity', 'Opacity at highest pressure', 0, 1, 2)
            self.left_vbox.pack_start(min_opacity_control.control, False, False)
            self.right_vbox.pack_start(max_opacity_control.control, False, False)
            self.brush_controls += [min_opacity_control, max_opacity_control]

        if brush_type==BrushType.Smudge:
            smudge_amount_control = BrushSettingControl(self, 'smudge_amount', 'Smudge amount', 0, 1, 2)
            self.left_vbox.pack_start(smudge_amount_control.control, False, False)
            self.brush_controls += [smudge_amount_control]

        step_control = BrushSettingControl(self, 'step', 'Step', 1, 15, 0)
        self.left_vbox.pack_start(step_control.control, False, False)
        self.brush_controls += [step_control]

    def get_row_for_brush(self, brush_data):
        for group_row in self.treestore:
            for brush_row in group_row.iterchildren():
                if brush_row[0]==brush_data:
                    return brush_row
        return None


    def setup_treestore(self):
        self.treestore = gtk.TreeStore(object, str, bool, int)
        for brush_group in self.brush_manager.brush_groups:
            brush_group_node = self.treestore.append(None, self.create_row_for_brush_group(brush_group))
            for brush_data in brush_group.brushes:
                self.treestore.append(brush_group_node, self.create_row_for_brush(brush_data))

        self.treeview.set_model(self.treestore)

    def create_row_for_brush_group(self, group):
        return [None, group.name, False, pango.WEIGHT_BOLD]

    def create_row_for_brush(self, brush):
        return [brush, brush.name, not brush.is_original, self.font_weight_for_brush(brush)]

    def font_weight_for_brush(self, brush):
        if brush.is_original:
            return pango.WEIGHT_BOLD
        return pango.WEIGHT_NORMAL


    def setup_treeview(self):
        brush_name_column = gtk.TreeViewColumn('Brush')
        self.treeview.append_column(brush_name_column)
        brush_cell = gtk.CellRendererText()
        brush_name_column.pack_start(brush_cell, True)
        brush_name_column.add_attribute(brush_cell, 'text', 1)
        brush_name_column.add_attribute(brush_cell, 'editable', 2)
        brush_name_column.add_attribute(brush_cell, 'weight', 3)
        brush_cell.connect('edited', self.brush_name_changed, self.treestore)

    def set_controls_for_brush_group(self, group_name):
        self.brush_group_controls.show()
        self.brush_settings_controls.hide()
        self.restore_brush_settings_button.hide()
        self.brush_group_name_label.set_text(group_name)

    def set_controls_for_brush(self, brush_data):
        self.brush_group_controls.hide()
        self.brush_settings_controls.show()
        self.restore_brush_settings_button.show()
        self.brush_type_combobox.set_active(find_item(self.liststore, lambda(row): row[0]==brush_data.brush_type).path[0])
        self.set_brush_data_for_all_brush_controls(brush_data)

    def on_brush_list_treeview_cursor_changed(self, widget, data=None):
        brush_data = self.treestore.get_value(self.treestore.get_iter(self.current_path()), 0)
        if not brush_data:
            self.set_controls_for_brush_group(self.treestore.get_value(self.treestore.get_iter(self.current_path()), 1))
        else:
            self.set_controls_for_brush(brush_data)
            self.brush_manager.select_brush(brush_data)


    def on_brush_management_form_delete_event(self, widget, data=None):
        self.hide()
        return True

    def on_brush_list_treeview_button_press_event(self, widget, data=None):
        if data.button==3:
            pthinfo = self.treeview.get_path_at_pos(int(data.x), int(data.y))
            if pthinfo is not None:
                path = pthinfo[0]
                brush_data = self.treestore[path][0]
                if brush_data:
                    self.treeview.grab_focus()
                    self.treeview.set_cursor( path, self.treeview.get_column(0), 0)
                    self.delete_brush_menu_item.set_sensitive(self.treestore[path][2])
                    self.rename_brush_menu_item.set_sensitive(self.treestore[path][2])
                    self.brush_list_menu.show_all()
                    self.brush_list_menu.popup( None, None, None, data.button, data.time)

    def on_delete1_activate(self, widget, data=None):
        current_iter = self.treestore.get_iter(self.current_path())
        self.brush_manager.remove_brush(self.treestore.get_value(current_iter, 0))
        self.treestore.remove(current_iter)

    def on_copy1_activate(self, widget, data=None):
        current_iter = self.treestore.get_iter(self.current_path())
        brush_data = self.treestore.get_value(current_iter, 0)
        new_brush_data = brush_data.create_copy()
        new_brush_data.name = '%(brushname)s Copy' % {'brushname' : brush_data.name}
        self.brush_manager.add_brush(self.brush_manager.group_for_brush(brush_data), new_brush_data)
        new_iter = self.treestore.append(self.treestore.iter_parent(current_iter), self.create_row_for_brush(new_brush_data))
        self.treeview.set_cursor(self.treestore.get_path(new_iter))

    def on_rename1_activate(self, widget, data=None):
        self.treeview.set_cursor(self.current_path(), self.treeview.get_column(0), True)

    def on_restore_brush_settings_button_clicked(self, widget, data=None):
        brush_data = self.treestore[self.current_path()][0]
        brush_data.restore_from_originals()
        self.set_controls_for_brush(brush_data)



    def brush_name_changed(self, cell, path, new_text, user_data):
        self.treestore[path][0].name = new_text
        self.treestore[path][1] = new_text
        self.brush_manager.on_brush_name_changed(self.treestore[path][0])


    def current_path(self):
        return self.treeview.get_cursor()[0]

    def get_current_brush_data(self):
        return self.treestore[self.current_path()][0]


    def on_brush_type_combobox_changed(self, widget, data=None):
        new_type = self.liststore[self.brush_type_combobox.get_active()][0]
        if self.brush_manager.active_brush_data.brush_type == new_type:
            return
        brush_data = self.treestore[self.current_path()][0]
        brush_data.brush_type = new_type
        self.create_controls_for_brush_type(brush_data.brush_type)

