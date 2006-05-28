# brushmanagementdialog.py
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
import gobject
from goghtooldialog import GoghToolDialog
from goghutil import *

class BrushManagementDialog(GoghToolDialog):
    def __init__(self):
        xml = gtk.glade.XML("glade/goghglade.glade", root="brush_management_form")
        xml.signal_autoconnect(self)  
        self.dialog = xml.get_widget("brush_management_form")
        self.brush_list_treeview = xml.get_widget("brush_list_treeview")
        
        self.treestore = gtk.TreeStore(str)
        for parent in range(4):
            piter = self.treestore.append(None, ['parent %i' % parent])
            for child in range(3):
                self.treestore.append(piter, ['child %i of parent %i' % (child, parent)])
        self.brush_list_treeview.set_model(self.treestore)
        
        self.column = gtk.TreeViewColumn('Column 0')
        self.brush_list_treeview.append_column(self.column)
        self.cell = gtk.CellRendererText()
        self.column.pack_start(self.cell, True)
        self.column.add_attribute(self.cell, 'text', 0)
        self.brush_list_treeview.set_search_column(0)
        self.column.set_sort_column_id(0)
        self.brush_list_treeview.set_reorderable(True)
