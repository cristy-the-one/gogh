# settingmanager.py
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

import os
import os.path

import xml.dom.minidom
import xml.dom.ext

def load_brush_list_xmldoc():
    custom_path = os.path.join(os.path.expanduser('~'),'.gogh','brushlist.xml')
    if os.path.exists(custom_path):
        return xml.dom.minidom.parse(custom_path)
    return xml.dom.minidom.parse("brushlist.xml")
    
    
def create_settings_directory():
    path = os.path.join(os.path.expanduser('~'),'.gogh')
    if not os.path.exists(path):
        os.mkdir(path)
        
        
def save_brush_list_xmldoc(doc):
    create_settings_directory()    
    save_path = os.path.join(os.path.expanduser('~'),'.gogh','brushlist.xml')
    f = open(save_path, "w")
    xml.dom.ext.PrettyPrint(doc, f)
    f.close()

   


    
