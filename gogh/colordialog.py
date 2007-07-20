# colordialog.py
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

from goghtooldialog import GoghToolDialog

class ColorDialog(GoghToolDialog):
    def __init__(self):
        self.dialog = gtk.ColorSelectionDialog(_("Select Color"))
        self.dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.dialog.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_UTILITY)
        self.dialog.colorsel.set_current_color(gtk.gdk.Color(0))
        self.dialog.connect("delete-event", self.on_dialog_delete_event)
        self.colorsel = self.dialog.colorsel
        self.dialog.ok_button.hide()
        self.dialog.cancel_button.hide()
        self.check_menu_item = None

    def on_dialog_delete_event(self, widget, data=None):
        self.hide()
        return True
