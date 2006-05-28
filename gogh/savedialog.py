# savedialog.py
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
import os.path
from goghutil import *

class SaveDialog:
    def __init__(self, goghdoc):
        self.formats = { 0 : 'GOGH', 1 : 'PNG', 2 : 'JPEG' }
        self.extensions = { 0 : 'gogh', 1 : 'png', 2 : 'jpeg' }
        self.goghdoc = goghdoc
        xml = gtk.glade.XML("glade/goghglade.glade", root="save_as_dialog")
        xml.signal_connect("on_file_type_combo_changed",self.on_file_type_combo_changed)  
        self.save_dialog = xml.get_widget("save_as_dialog")
        self.save_dialog.set_current_name(self.goghdoc.document_name)
        self.file_type_combo = xml.get_widget("file_type_combo")
        self.file_type_combo.set_active(0)
        
    def on_file_type_combo_changed(self, widget, data=None): 
        filename = os.path.split(self.save_dialog.get_filename())[1]
        s = replace_extension(filename, self.get_extension())
        self.save_dialog.set_current_name(s)
        
    def save_current_document(self, format, filename):
        if format=='GOGH':
            self.goghdoc.document_name = filename
            self.goghdoc.save(self.goghdoc.document_name)
        if format=='PNG':
            self.goghdoc.composite.save(filename, 'png')
        if format=='JPEG':
            self.goghdoc.composite.save(filename, 'jpeg')
            
    def get_save_format(self):
        return self.formats[self.file_type_combo.get_active()]
        
    def get_extension(self):
        return self.extensions[self.file_type_combo.get_active()]

    def show(self):
        response = self.save_dialog.run()
        if response == gtk.RESPONSE_OK:
            self.save_current_document(self.get_save_format(), self.save_dialog.get_filename())
        self.save_dialog.destroy()      
        

