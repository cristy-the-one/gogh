# settingmanager.py
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

import os
import os.path

import xml.dom.minidom
import xml.dom.ext

from goghutil import get_abspath

def load_custom_brush_list_xmldoc():
    custom_path = os.path.join(get_settings_path() ,'custom_brushlist.xml')
    if os.path.exists(custom_path):
        return xml.dom.minidom.parse(custom_path)
    return None
    
def load_original_brush_list_xmldoc():
    return xml.dom.minidom.parse(get_abspath("brushlist.xml"))
    custom_path = os.path.join(get_settings_path() ,'custom_brushlist.xml')
    
def create_settings_directory():
    path = os.path.join(get_settings_path())
    if not os.path.exists(path):
        os.mkdir(path)
        
def get_settings_path():
    return os.path.join(os.path.expanduser('~'),'.gogh')
        
        
def save_brush_list_xmldoc(doc):
    try:
        save_path = os.path.join(get_settings_path(), 'custom_brushlist.xml')
        create_settings_directory()    
        f = open(save_path, "w")
        xml.dom.ext.PrettyPrint(doc, f)
        f.close()
    except:
        print 'Cannot save custom brush list'
        

   


    
