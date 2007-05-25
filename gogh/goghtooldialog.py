# goghtooldialog.py
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

import goghglobals

class GoghToolDialog:
    def __init__(self):
        self.dialog = None
        self.check_menu_item = None

    def assign_check_menu_item(self, check_menu_item):
        self.check_menu_item = check_menu_item
        self.check_menu_item.connect("toggled", self.menu_item_toggled)

    def menu_item_toggled(self, widget, data=None):
        self.dialog.set_transient_for(goghglobals.gogh_main_window)
        if self.check_menu_item.get_active():
            self.dialog.show()
        else:
            self.dialog.hide()

    def show(self):
        self.dialog.set_transient_for(goghglobals.gogh_main_window)
        self.dialog.show()
        if self.check_menu_item:
            self.check_menu_item.set_active(True)

    def hide(self):
        self.dialog.hide()
        if self.check_menu_item:
            self.check_menu_item.set_active(False)
