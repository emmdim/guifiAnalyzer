#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# guifinet_studio.py - Explore your free network offline!
# Copyright (C) 2011-2012 Pablo Castellano <pablo@anche.no>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from gi.repository import GtkClutter, Clutter
GtkClutter.init([]) # Must be initialized before importing those:
from gi.repository import Gdk, Gtk
from gi.repository import GtkChamplain, Champlain

import os
import sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.append('lib')

from libcnml import CNMLParser, Status
import pyGuifiAPI
from pyGuifiAPI.error import GuifiApiError

from configmanager import GuifinetStudioConfig
from unsolclic import UnSolClic
from utils import *

from urllib2 import URLError

class GuifinetStudio:
	def __init__(self, cnmlFile="tests/detail.3"):
		self.currentView = 0
		self.cnmlFile = cnmlFile
		self.points_layer = None
		self.labels_layer = None
		
		# Unsolclic instance
		self.usc = UnSolClic()

		# UI Widgets
		self.ui = Gtk.Builder()
		self.ui.add_from_file('guifinet_studio.ui')
		self.ui.connect_signals(self)

		self.mainWindow = self.ui.get_object('mainWindow')
		self.listNodesWindow = self.ui.get_object('listNodesWindow')
		
		self.nodesList = self.ui.get_object("scrolledwindow1")
		self.treestore = self.ui.get_object("treestore1")
		self.treeview = self.ui.get_object("treeview1")
		self.treeview2 = self.ui.get_object("treeview2")
		self.treestore2 = self.ui.get_object("treestore2")
		self.statusbar = self.ui.get_object("statusbar1")
		self.actiongroup1 = self.ui.get_object("actiongroup1")
		self.menuitem6 = self.ui.get_object("menuitem6")

		self.embedBox = self.ui.get_object("embedBox")
		self.notebook1 = self.ui.get_object("notebook1")
		self.notebook1.set_show_tabs(False)
		
		self.embed = GtkChamplain.Embed()
		self.embed.set_size_request(640, 480)
		
		self.view = self.embed.get_view()
		self.view.set_reactive(True)
		self.view.set_kinetic_mode(True)
		self.view.set_zoom_level(13)
		self.view.center_on(36.72341, -4.42428)
		self.view.connect('button-release-event', self.mouse_click_cb)
		
		scale = Champlain.Scale()
		scale.connect_view(self.view)
		self.view.bin_layout_add(scale, Clutter.BinAlignment.START, Clutter.BinAlignment.END)

		self.box1 = self.ui.get_object('box1')
		self.paned = self.ui.get_object("paned1")
		self.paned.pack2(self.embed, True, True)
#		self.embedBox.pack_start(self.embed, True, True, 0)
#		self.embedBox.reorder_child(self.embed, 0)
		
		self.uimanager = Gtk.UIManager()
		self.uimanager.add_ui_from_file("guifinet_studio_menu.ui")
		self.uimanager.insert_action_group(self.actiongroup1)
		self.menu1 = self.uimanager.get_widget("/KeyPopup1")
		self.menu2 = self.uimanager.get_widget("/KeyPopup2")

		self.t6 = self.ui.get_object("treeviewcolumn6")
		self.nodedialog = self.ui.get_object("nodeDialog")

		# preferences dialog
		self.preferencesdialog = self.ui.get_object('preferencesdialog')
		self.userentry = self.ui.get_object('userentry')
		self.passwordentry = self.ui.get_object('passwordentry')
		self.defaultzonecombobox = self.ui.get_object('defaultzonecombobox')
		self.defaultzoneentry = self.ui.get_object('defaultzoneentry')
		self.entrycompletion2 = self.ui.get_object('entrycompletion2')
		
		# unsolclic dialog
		self.uscdialog = self.ui.get_object("uscdialog")
		self.usctextbuffer = self.ui.get_object("usctextbuffer")
		
		# edit node dialog
		self.editnodeokbutton = self.ui.get_object("editnodeokbutton")
		self.editnodedialog = self.ui.get_object("editnodedialog")
		self.nodecoordinatesentry = self.ui.get_object('nodecoordinatesentry')
		self.nodetitleentry = self.ui.get_object('nodetitleentry')		
		self.nodeinfotextview = self.ui.get_object('nodeinfotextview')
		self.nodenickentry = self.ui.get_object('nodenickentry')
		self.nodecontactentry = self.ui.get_object('nodecontactentry')
		self.nodezonecombobox = self.ui.get_object('nodezonecombobox')
		self.nodezonedescentry = self.ui.get_object('nodezonedescentry')
		self.nodeelevationentry = self.ui.get_object('nodeelevationentry')
		self.nodegraphscombobox = self.ui.get_object('nodegraphscombobox')
		self.takefromparentscheckbutton = self.ui.get_object('takefromparentscheckbutton')
		self.stablenodecheckbutton = self.ui.get_object('stablenodecheckbutton')
		self.entrycompletion1 = self.ui.get_object('entrycompletion1')
		self.nodeinfotextbuffer = self.ui.get_object('nodeinfotextbuffer')
		
		# edit zone dialog
		self.editzonedialog = self.ui.get_object('editzonedialog')
		self.parentzonecombobox = self.ui.get_object('parentzonecombobox')
		
		# edit device dialog
		self.editdevicedialog = self.ui.get_object('editdevicedialog')
		self.editdevicenodecombobox = self.ui.get_object('editdevicenodecombobox')
		
		# edit radio dialog
		self.editradiodialog = self.ui.get_object('editradiodialog')
		self.editradionodecombobox = self.ui.get_object('editradionodecombobox')
		
		# edit interface dialog
		self.editinterfacedialog = self.ui.get_object('editinterfacedialog')
		
		# edit link dialog
		self.editlinkdialog = self.ui.get_object('editlinkdialog')
		self.editlinknode1combobox = self.ui.get_object('editlinknode1combobox')
		self.editlinknode2combobox = self.ui.get_object('editlinknode2combobox')
		
		# file chooser dialog
		self.opendialog = self.ui.get_object("filechooserdialog1")
		self.opendialog.set_action(Gtk.FileChooserAction.OPEN)
		
		# about dialog
		self.about_ui = self.ui.get_object("aboutdialog1")

		# cnml dialog
		self.cnmldialog = self.ui.get_object('cnmldialog')
		self.treeview4 = self.ui.get_object('treeview4')
		
		# configuration
		self.configmanager = GuifinetStudioConfig()

		# Guifi.net API
		self.guifiAPI = pyGuifiAPI.GuifiAPI(self.configmanager.getUsername(), self.configmanager.getPassword())
		self.authenticated = False
		
		with open("COPYING") as f:
			self.about_ui.set_license(f.read())

		try:
			self.cnmlp = CNMLParser(self.cnmlFile)
			self.completaArbol()
			self.paintMap()
		except IOError:
			self.statusbar.push(0, "CNML file \"%s\" couldn't be loaded" %self.cnmlFile)
			self.cnmlFile = None

		# Descargar siempre?
		self.allZones = []
		cnmlGWfile = self.configmanager.pathForCNMLCachedFile(GUIFI_NET_WORLD_ZONE_ID, 'zones')
		self.zonecnmlp = CNMLParser(cnmlGWfile)
		for z in self.zonecnmlp.getZones():
			self.allZones.append((z.id, z.title))
		
		self.mainWindow.show_all()
		self.authAPI()


	def add_node_point(self, layer, lat, lon, size=12):
		p = Champlain.Point.new()
		p.set_location(lat, lon)
		p.set_size(size)
		layer.add_marker(p)
	
	
	def add_node_label(self, layer, lat, lon, nombre):
		p = Champlain.Label.new()
		p.set_text(nombre)
		color = Clutter.Color.new(0, 0, 0, 255)
		p.set_text_color(color)
		p.set_location(lat, lon)
		p.set_draw_background(False)
		layer.add_marker(p)

	
	# Two layers:
	#  1) Points only
	#  2) Labels only
	def paintMap(self):
		self.points_layer = Champlain.MarkerLayer()
		self.points_layer.set_selection_mode(Champlain.SelectionMode.SINGLE)
		self.labels_layer = Champlain.MarkerLayer()

		nodes = self.cnmlp.getNodes()

		for n in nodes:
			self.add_node_point(self.points_layer, n.latitude, n.longitude)
			self.add_node_label(self.labels_layer, n.latitude, n.longitude, n.title)
		
		# It's important to add points the last. Points are selectable while labels are not
		# If labels is added later, then you click on some point and it doesn't get selected
		# because you are really clicking on the label. Looks like an usability bug?
		self.view.add_layer(self.labels_layer)
		self.view.add_layer(self.points_layer)
		

	def completaArbol(self):
		self.treestore.clear()
		self.treestore2.clear()
		# Add root zone
		parenttree = self.__addZoneToTree(self.cnmlp.rootzone, None)
		self.__addNodesFromZoneToTree(self.cnmlp.rootzone, parenttree)
		
		# Iter for every zone (except root) and adds them with nodes to the TreeView
		self.__completaArbol_recursive(self.cnmlp.rootzone, parenttree)
										
		self.treeview.expand_all()
		
		self.treestore.set_sort_column_id (5, Gtk.SortType.ASCENDING)
		self.treestore2.set_sort_column_id (0, Gtk.SortType.ASCENDING)
		self.statusbar.push(0, "Loaded CNML succesfully")


	# Recursive
	def __completaArbol_recursive(self, parentzid, parenttree):
		zones = self.cnmlp.getSubzonesFromZone(parentzid)
		
		for z in zones:
			tree = self.__addZoneToTree(z.id, parenttree)
			self.__addNodesFromZoneToTree(z.id, tree)
			self.__completaArbol_recursive(z.id, tree)
			
		
	def __addZoneToTree(self, zid, parentzone):
		
		# Given a list of node ids, counts how many of them are for each status (working, planned...)
		def countNodes(nodes):
			nodescount = dict()
			nodescount[Status.UNKNOWN] = 0
			nodescount[Status.PLANNED] = 0
			nodescount[Status.WORKING] = 0
			nodescount[Status.TESTING] = 0
			nodescount[Status.BUILDING] = 0
			
			for n in nodes:
				st = n.status
				nodescount[st] += 1
				
			try:
				assert nodescount[Status.UNKNOWN] == 0
			except AssertionError:
				print 'There are %d nodes with status == UNKNOWN' %nodescount[Status.UNKNOWN]
				
			return (nodescount[Status.PLANNED], nodescount[Status.WORKING], nodescount[Status.TESTING], nodescount[Status.BUILDING])

		zone = self.cnmlp.getZone(zid)
		nodes = zone.getNodes()
		
		col1 = "%s (%d)" %(zone.title, len(nodes))
		(nplanned, nworking, ntesting, nbuilding) = countNodes(nodes)

		# Add a new row for the zone
		row = (col1, str(nworking), str(nbuilding), str(ntesting), str(nplanned), None, None)
		tree = self.treestore.append(parentzone, row)
		return tree
		
		
	def __addNodesFromZoneToTree(self, zid, parentzone):
		nodes = self.cnmlp.getNodesFromZone(zid)
		for n in nodes:
			row = (None, None, None, None, None, n.title, n.id)
			self.treestore.append(parentzone, row)
			self.treestore2.append(None, (n.title, n.id))
		

	def on_showPointsButton_toggled(self, widget, data=None):
		print 'Show points:', widget.get_active()	
		if widget.get_active():
			self.points_layer.show_all_markers()
		else:
			self.points_layer.hide_all_markers()

	
	def on_showLabelsButton_toggled(self, widget, data=None):
		print 'Show labels:', widget.get_active()
		if widget.get_active():
			self.labels_layer.show_all_markers()
		else:
			self.labels_layer.hide_all_markers()
	
	
	def on_showLinksButton_toggled(self, widget, data=None):
		print 'Show links:', widget.get_active()
	

	def on_showZonesButton_toggled(self, widget, data=None):
		print 'Show zones:', widget.get_active()
		
		
	def on_updatezonesmenuitem_activate(self, widget, data=None):
		try:
			fp = self.guifiAPI.downloadCNML(GUIFI_NET_WORLD_ZONE_ID, 'zones')
			zone_filename = '%d.cnml' %GUIFI_NET_WORLD_ZONE_ID
			filename = os.path.join(self.configmanager.CACHE_DIR, 'zones', zone_filename)
			with open(filename, 'w') as zonefile:
				zonefile.write(fp.read())
		except URLError, e:
			g = Gtk.MessageDialog(None, Gtk.DialogFlags.MODAL, Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE, 
								"Error accessing to the Internets:\n" + str(e.reason))
			g.set_title('Error downloading CNML')
			g.run()
			g.destroy()

		
	def on_action1_activate(self, action, data=None):
		self.nodedialog.show()
		self.nodedialog.set_title("Information about node XXX")


	def on_action2_activate(self, action, data=None):
		Gtk.show_uri(None, "http://guifi.net/node/", Gtk.get_current_event_time())
		

	def on_action3_activate(self, action, data=None):
		print 'View in map'


	def on_treeviewcolumn6_clicked(self, action, data=None):
		#print action.get_sort_column_id()
		(column_id, sorttype) = self.treestore.get_sort_column_id()
		name = action.get_name()
		
		if sorttype == Gtk.SortType.ASCENDING:
			sorttype = Gtk.SortType.DESCENDING
		else:
			sorttype = Gtk.SortType.ASCENDING
			
		# 'treeview1, treeview2, treeview3, ..., treeview6
		column_id = int(name[-1]) -1
		
		self.treestore.set_sort_column_id (column_id, sorttype)
	
	
	def on_action4_activate(self, action, data=None):
		# get node id
		sel = self.treeview.get_selection()
		(model, it) = sel.get_selected()
		nid = model.get_value(it, 6)
			
		# Varias interfaces - varios unsolclic
		# TODO: Ventana con la interfaz seleccionable que quieras generar
		devices = self.cnmlp.nodes[nid].devices
		
		if devices == {}:
			g = Gtk.MessageDialog(None, Gtk.DialogFlags.MODAL, Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE, 
								"Couldn't generate unsolclick.\nThe node doesn't have any device defined.")
			g.set_title('Error generating unsolclic')
			g.run()
			g.destroy()
			return
		elif len(devices) > 1:
			g = Gtk.MessageDialog(None, Gtk.DialogFlags.MODAL, Gtk.MessageType.WARNING, Gtk.ButtonsType.CLOSE, 
								"Several devices in this node. Generating just the first one.")
			g.set_title('Warning generating unsolclic')
			g.run()
			g.destroy()
		
		node = self.cnmlp.nodes[nid]
		conf = self.usc.generate(node)
		
		self.uscdialog.show()
		#self.uscdialog.set_title("Unsolclic for device "+model.get_value(it, 5))
		self.uscdialog.set_title("Unsolclic for node "+node.title)
		self.usctextbuffer.set_text(conf)
		
		
	def on_nodeDialog_delete_event(self, widget, data=None):
		self.nodedialog.hide()
		return True

	def on_cnmldialog_delete_event(self, widget, data=None):
		self.cnmldialog.hide()
		return True
		
	def on_autoloaduscbutton_clicked(self, widget, data=None):
		print 'Autoload configuration'
		raise NotImplementedError
		

	def on_uscsave_clicked(self, widget, data=None):
		raise NotImplementedError
		
	def on_copyuscbutton_clicked(self, widget, data=None):
		print 'copy usc to clipboard'
		#cb = Gtk.Clipboard()
		#cb.set_text(self.usctextbuffer.get_text(), -1)
		self.usctextbuffer.copy_clipboard(Gtk.Clipboard.get(Gdk.Atom.intern('0', True)))
		raise NotImplementedError
		

	def on_uscdialog_delete_event(self, widget, data=None):
		self.uscdialog.hide()
		return True


	def on_menuitem5_toggled(self, widget, data=None):
		isActive = widget.get_active()
		
		if isActive:
			self.statusbar.show()
		else:
			self.statusbar.hide()


	def on_menuitem6_toggled(self, widget, data=None):
		isActive = widget.get_active()
		
		if isActive:
			self.box1.show()
		else:
			self.box1.hide()
		
		
		
	def on_button5_clicked(self, widget, data=None):
		self.box1.hide()
		self.menuitem6.set_active(False)
		

	def on_treeview1_button_release_event(self, widget, data=None):
		sel = widget.get_selection()
		(model, it) = sel.get_selected()

		if it is None: # treeview is clear
			return True
			
		col = widget.get_path_at_pos(int(data.x), int(data.y))[1]
		
		if data.button == 3: # Right button
			if col is self.t6 and model.get_value(it, 5) is not None: 
				#user clicked on a node
				self.menu1.popup(None, None, None, None, data.button, data.time)
	

	def on_treeview2_button_release_event(self, widget, data=None):
		sel = widget.get_selection()
		(model, it) = sel.get_selected()
		
		if it is None: # treeview is clear
			return True
		
		if data.button == 1: # Right button
			nid = model.get_value(it, 1)
			lat = float(self.cnmlp.getNode(nid).latitude)
			lon = float(self.cnmlp.getNode(nid).longitude)
			self.view.center_on(lat, lon)
			#self.view.go_to(lat, lon)
		
	
	def on_treeview2_key_press_event(self, widget, data=None):
		sel = widget.get_selection()
		(model, it) = sel.get_selected()
		
		if data.keyval == Gdk.KEY_space or data.keyval == Gdk.KEY_KP_Space	or data.keyval == Gdk.KEY_Return or data.keyval == Gdk.KEY_KP_Enter:
			nid = model.get_value(it, 1)
			lat = float(self.cnmlp.getNode(nid).latitude)
			lon = float(self.cnmlp.getNode(nid).longitude)
			self.view.center_on(lat, lon)
			#self.view.go_to(lat, lon)
		

	def on_imagemenuitem2_activate(self, widget, data=None):
		self.opendialog.run()

	def on_imagemenuitem3_activate(self, widget, data=None):
		self.treestore.clear()
		self.treestore2.clear()
		self.points_layer.remove_all()
		self.labels_layer.remove_all()
		self.statusbar.push(0, "Closed CNML file")
		self.cnmlFile = None
		
	def on_button3_clicked(self, widget, data=None):
		self.cnmlFile = self.opendialog.get_filename()
		print self.cnmlFile
		self.opendialog.hide()

		try:
			self.cnmlp = CNMLParser(self.cnmlFile)
			self.completaArbol()
			self.paintMap()
		except IOError:
			self.statusbar.push(0, "CNML file \"%s\" couldn't be loaded" %self.cnmlFile)
			self.cnmlFile = None
			

	def on_aboutdialog1_close(self, widget, data=None):
		self.about_ui.hide()
		return True


	def on_imagemenuitem10_activate(self, widget, data=None):
		self.about_ui.show()


	def on_changeViewButton_toggled(self, widget, data=None):		
		if self.currentView == 0:
			self.currentView = 1
		else:
			self.currentView = 0
		self.notebook1.set_current_page(self.currentView)
		
		
	def zoom_in(self, widget, data=None):
		self.view.zoom_in()
		
		
	def zoom_out(self, widget, data=None):
		self.view.zoom_out()
		
		
	def gtk_main_quit(self, widget, data=None):
		Gtk.main_quit()
	
	def on_preferencesmenuitem_activate(self, widget ,data=None):
		self.preferencesdialog.show()
		self.userentry.set_text(self.configmanager.getUsername())
		self.passwordentry.set_text(self.configmanager.getPassword())
		self.fillZonesComboBox(self.defaultzonecombobox, self.entrycompletion2)
		
	def on_preferencesdialog_delete_event(self, widget, data=None):
		self.preferencesdialog.hide()
		# TODO: Save changed preferences
		return True
		
	def on_createnodemenuitem_activate(self, widget=None, data=None):
		self.editnodedialog.set_title('Create new Guifi.net node')
		self.fillZonesComboBox(self.nodezonecombobox, self.entrycompletion1)
		self.editnodedialog.show()
		
	def on_editnodedialog_delete_event(self, widget, data=None):
		self.editnodedialog.hide()
		return True
		
	def on_createzonemenuitem_activate(self, widget, data=None):
		self.editzonedialog.set_title('Create new Guifi.net zone')
		self.fillZonesComboBox(self.parentzonecombobox)
		self.editzonedialog.show()
		
	def on_editzonedialog_delete_event(self, widget, data=None):
		self.editzonedialog.hide()
		return True
	
	def on_createdevicemenuitem_activate(self, widget, data=None):
		self.editdevicedialog.set_title('Create new Guifi.net device')
		self.fillNodesComboBox(self.editdevicenodecombobox)
		self.editdevicedialog.show()
		
	def on_editdevicedialog_delete_event(self, widget, data=None):
		self.editdevicedialog.hide()
		return True
	
	def on_createradiomenuitem_activate(self, widget, data=None):
		self.editradiodialog.set_title('Create new Guifi.net radio')
		self.fillNodesComboBox(self.editradionodecombobox)
		self.editradiodialog.show()
		
	def on_editradiodialog_delete_event(self, widget, data=None):
		self.editradiodialog.hide()
		return True
		
	def on_createinterfacemenuitem_activate(self, widget, data=None):
		self.editinterfacedialog.set_title('Create new Guifi.net interface')
		self.editinterfacedialog.show()
	
	def on_editinterfacedialog_delete_event(self, widget, data=None):
		self.editinterfacedialog.hide()
		return True
		
	def on_createlinkmenuitem_activate(self, widget, data=None):
		self.editlinkdialog.set_title('Create new Guifi.net link')
		self.fillNodesComboBox(self.editlinknode1combobox)
		self.fillNodesComboBox(self.editlinknode2combobox)
		self.editlinkdialog.show()
		
	def on_editlinkdialog_delete_event(self, widget, data=None):
		self.editlinkdialog.hide()
		return True
		
	def mouse_click_cb(self, widget, event):
		# event == void (GdkEventButton?)
		if event.button == 3: # Right button
			X, Y = event.x, event.y
			self.lon, self.lat = self.view.x_to_longitude(X), self.view.y_to_latitude(Y)
			self.menu2.popup(None, None, None, None, event.button, event.time)

	def on_action5_activate(self, action, data=None):
		self.nodecoordinatesentry.set_text(str(self.lat) + ', ' + str(self.lon))
		self.nodecoordinatesentry.set_sensitive(False)
		del self.lat, self.lon
		self.nodetitleentry.grab_focus()
		self.on_createnodemenuitem_activate()
	
	def on_acceptxolncheckbutton_toggled(self, widget, data=None):
		isActive = widget.get_active()
		self.editnodeokbutton.set_sensitive(isActive)
		
	def editnodevalidation(self):
		# Checks: title, zone, lat, lon
		if self.nodetitleentry.get_text() == '':
			self.nodetitleentry.grab_focus()
			return False
		
		if not valid_email_address(self.nodecontactentry.get_text()):
			self.nodecontactentry.grab_focus()
			return False
			
		if self.nodecoordinatesentry.get_text() == '':
			self.nodecoordinatesentry.grab_focus()
			return False
		else:
			try:
				lat,lon = self.nodecoordinatesentry.get_text().split(',')
				if lat == '' or lon == '':
					self.nodecoordinatesentry.grab_focus()
					return False
				float(lat)
				float(lon)
			except ValueError:
				self.nodecoordinatesentry.grab_focus()
				return False
				
		if self.nodezonecombobox.get_active_iter() is None:
			self.nodezonecombobox.grab_focus()
			return False
		
		if not self.takefromparentscheckbutton.get_active() and self.nodegraphscombobox.get_active_iter() is None:
			return False
			
		# rest of value types
		try:
			if self.nodeelevationentry.get_text() != '':
				int(self.nodeelevationentry.get_text())
		except ValueError, e:
			self.nodeelevationentry.grab_focus()
			return False
			
		return True
		
	def on_takefromparentscheckbutton_toggled(self, widget, data=None):
		isActive = widget.get_active()
		self.nodegraphscombobox.set_sensitive(not isActive)
		
	def on_editnodeokbutton_clicked(self, widget, data=None):
		"""
		nodegraphscombobox

		status?
		"""

		(start, end) = self.nodeinfotextbuffer.get_bounds()
		nodeinfotext = self.nodeinfotextview.get_buffer().get_text(start, end, True)
		
		if not self.editnodevalidation():
			print "There's some invalid data"
			return
		
		lat,lon = self.nodecoordinatesentry.get_text().split(',')
		it = self.nodezonecombobox.get_active_iter()
		zid = self.nodezonecombobox.get_model().get_value(it, 0)
		if self.takefromparentscheckbutton.get_active():
			graphs = None
		else:
			it = self.nodegraphscombobox.get_active_iter()
			graphs = self.nodegraphscombobox.get_model().get_value(it, 0)
		
		
		
		messagestr = 'You are about to create the node named "%s".\nPlease choose where you want to create it' %self.nodetitleentry.get_text()
		
		# Messagebox (internet / local / cancelar)
		g = Gtk.MessageDialog(None, Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.QUESTION, Gtk.ButtonsType.CANCEL, messagestr)
		g.set_title('Confirmation')
		g.add_button('Create locally\n(CNML)', -12)
		g.add_button('Create remotely\n(%s)' %self.guifiAPI.getHost(), -13)
		response = g.run()
		g.destroy()
		
		print response # ESC --> -4
		if response == Gtk.ResponseType.CANCEL:
			return
		
		try:
			node_id = self.guifiAPI.addNode(self.nodetitleentry.get_text(), zid, lat, lon, body=nodeinfotext,
						nick=self.nodenickentry.get_text(), zone_desc=self.nodezonedescentry.get_text(),
						notification=self.nodecontactentry.get_text(), elevation=self.nodeelevationentry.get_text(),
						stable=self.stablenodecheckbutton.get_active(), graph_server=graphs, status='Planned')
		except GuifiApiError, e:
			errormessage = 'Error %d: %s\n\nError message:\n%s' %(e.code, e.reason, e.extra)
			g = Gtk.MessageDialog(None, Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, errormessage)
			g.set_title('Response from server')
			g.run()
			g.destroy()
			return
		
		# Messagebox status
		
		url = self.guifiAPI.urlForNode(node_id)
		messagestr = 'Node succesfully created with id %d\n\nYou can view it in the following url:\n%s' %(node_id, url)
		g = Gtk.MessageDialog(None, Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.INFO, Gtk.ButtonsType.CLOSE, messagestr)
		g.add_button('Open in web browser', -12)
		g.set_title('Response from server')
		response = g.run()
		g.destroy()
		
		if response != Gtk.ResponseType.CLOSE:
			print 'Opening in web browser'
			systemstr = 'xdg-open %s' %url
			os.system(systemstr)
			
		self.editnodedialog.hide()
		
	
	def fillNodesComboBox(self, combobox):
		model = combobox.get_model()
		model.clear()
		model.set_sort_column_id (1, Gtk.SortType.ASCENDING)
		
		# zoneid - title
		for n in self.cnmlp.getNodes():
			model.append((n.id, n.title))
			
	def fillZonesComboBox(self, combobox=None, entrycompletion=None):
		# zoneid - title
		if combobox:
			model = combobox.get_model()
			model.clear()
			model.set_sort_column_id (1, Gtk.SortType.ASCENDING)
			model.append((0, '-- Most recently used --'))
			
			n = 0
			for z in self.cnmlp.getZones():
				n +=1
				model.append((z.id, z.title))
			combobox.set_active(n)
		
		if entrycompletion:
			model = entrycompletion.get_model()
			model.clear()
			for z in self.allZones:
				model.append((z[0], z[1]))
			
		
	def authAPI(self):
		try:
			self.guifiAPI.auth()
			self.authenticated = True
			self.statusbar.push(0, "Logged into Guifi.net")
		except URLError, e: # Not connected to the Internets
			self.statusbar.push(0, "Couldn't login into Guifi.net: check your Internet connection")
			self.authenticated = False
		except GuifiApiError, e:
			g = Gtk.MessageDialog(None, Gtk.DialogFlags.MODAL, Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE, 
								"Couldn't login into Guifi.net:\n" + e.reason)
			g.run()
			g.destroy()
			self.authenticated = False
		
	def fillAvailableCNMLModel(self, model):
		cnmls = dict()
		
		for d in ['nodes', 'zones', 'detail']:
			directory = os.path.join(self.configmanager.CACHE_DIR, d)
			filelist = os.listdir(directory)
			for f in filelist:
				zid, ext = f.split('.')
				zid = int(zid)
				if ext == 'cnml':
					if not cnmls.has_key('zid'):
						cnmls[zid] = dict()
						cnmls[zid]['nodes'] = False
						cnmls[zid]['zones'] = False
						cnmls[zid]['detail'] = False
					cnmls[zid][d] = True
		
		for zid in cnmls:			
			model.append((zid, self.zonecnmlp.getZone(zid).title, cnmls[zid]['nodes'], cnmls[zid]['zones'], cnmls[zid]['detail']))
				
		
	def on_downloadcnmlmenuitem_activate(self, widget, data=None):
		self.cnmldialog.show()
		# rellenar tabla
		self.fillAvailableCNMLModel(self.treeview4.get_model())
		
		
if __name__ == "__main__":

	if len(sys.argv) > 1:
		ui = GuifinetStudio(sys.argv[1])
	else:
		ui = GuifinetStudio()

	ui.mainWindow.show()
	Gtk.main()
