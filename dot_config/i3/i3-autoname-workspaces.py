#!/usr/bin/env python3

# This script listens for i3 events and updates workspace names to show icons
# for running programs.  It contains icons for a few programs, but more can
# easily be added by inserting them into WINDOW_ICONS below.
#
# Dependencies
# * xorg-xprop - install through system package manager
# * i3ipc - install with pip
# * fontawesome - install with pip
#
# Installation:
# * Download this script and place it in ~/.config/i3/ (or anywhere you want)
# * Add "exec_always ~/.config/i3/i3-autoname-workspaces.py &" to your i3 config
# * Restart i3: "$ i3-msg restart"
#
# Configuration:
# The default i3 config's keybingings reference workspaces by name, which is an
# issue when using this script because the "names" are constantaly changing to
# show window icons.  Instead, you'll need to change the keybindings to
# reference workspaces by number.  Change lines like:
#   bindsym $mod+1 workspace 1
# To:
#   bindsym $mod+1 workspace number 1


import re
import signal
import subprocess as proc
import sys

import fontawesome as fa
import i3ipc

# Add icons here for common programs you use.  The keys are the X window class
# (WM_CLASS) names (lower-cased) and the icons can be any text you want to
# display.
#
# Most of these are character codes for font awesome:
#   http://fortawesome.github.io/Font-Awesome/icons/
#
# If you're not sure what the WM_CLASS is for your application, you can use
# xprop (https://linux.die.net/man/1/xprop). Run `xprop | grep WM_CLASS`
# then click on the application you want to inspect.
WINDOW_ICONS = {
	'blender': fa.icons['cube'],
	'blueman-manager': fa.icons['bluetooth'],
	'calibre-gui': fa.icons['book'],
	'chromium': fa.icons['chrome'],
	'cities.x64': fa.icons['city'],
	'code': fa.icons['code'],
	'cutter': fa.icons['bug'],
	'darktable': fa.icons['camera'],
	'dwarf_fortress': fa.icons['fort-awesome'],
	'eclipse': fa.icons['code'],
	'emacs': fa.icons['code'],
	'evince': fa.icons['file-pdf'],
	'factorio': fa.icons['cog'],
	'feh': fa.icons['image'],
	'firefox': fa.icons['firefox'],
	'firefox-developer': fa.icons['firefox'],
	'ghb': fa.icons['video'],
	'gimp': fa.icons['file-image'],
	'gimp-2.10': fa.icons['file-image'],
	'google-chrome': fa.icons['chrome'],
	'gparted': fa.icons['hdd'],
	'gpicview': fa.icons['image'],
	'gsmartcontrol': fa.icons['hdd'],
	'inkscape': fa.icons['pen-nib'],
	'jetbrains-studio': fa.icons['code'],
	'kicad': fa.icons['microchip'],
	'roxterm': fa.icons['terminal'],
	'ksp.x86_64': fa.icons['space-shuttle'],
	'libreoffice-impress': fa.icons['file-powerpoint'],
	'libreoffice-writer': fa.icons['file-alt'],
	'lutris': fa.icons['gamepad'],
	'minecraft 1.12.2': fa.icons['cube'],
	'mirage': fa.icons['image'],
	'mpv': fa.icons['video'],
	'multimc': fa.icons['cube'],
	'mupdf': fa.icons['file-pdf'],
	'nemiver': fa.icons['bug'],
	'nm-connection-editor': fa.icons['wifi'],
	'org-openstreetmap-josm-gui-mainapplication': fa.icons['map'],
	'pavucontrol': fa.icons['volume-up'],
	'qbittorrent': fa.icons['download'],
	'qtcreator': fa.icons['code'],
	'rambox': fa.icons['comments'],
	'seahorse': fa.icons['lock'],
	'spotify': fa.icons['spotify'],
	'sqlectron': fa.icons['database'],
	'sqlitebrowser': fa.icons['database'],
	'steam': fa.icons['steam'],
	'subl': fa.icons['file-alt'],
	'subl3': fa.icons['file-alt'],
	'surviving mars': fa.icons['rocket'],
	'telegram-desktop': fa.icons['telegram'],
	'terraria.bin.x86_64': fa.icons['tree'],
	'thunderbird': fa.icons['envelope'],
	'vim': fa.icons['code'],
	'virt-manager': fa.icons['desktop'],
	'virtualbox manager': fa.icons['desktop'],
	'vivifyscrum': fa.icons['check'],
	'vlc': fa.icons['video'],
	'wire': fa.icons['comments'],
	'wireshark': fa.icons['network-wired'],
	'zathura': fa.icons['file-pdf'],
	'zenity': fa.icons['window-maximize'],
}

# This icon is used for any application not in the list above
DEFAULT_ICON = '*'


# Used so that we can keep the workspace's name when we add icons to it.
# Returns a dictionary with the following keys: 'num', 'shortname', and 'icons'
# Any field that's missing in @name will be None in the returned dict
def parse_workspace_name(name):
	match = re.match(r'(?P<num>\d+):?(?P<shortname>\w+)? ?(?P<icons>.+)?', name)
	return match.groupdict()


# Given a dictionary with 'num', 'shortname', 'icons', return the formatted name
# by concatenating them together.
def construct_workspace_name(parts):
	new_name = str(parts['num'])
	if parts['shortname'] or parts['icons']:
		new_name += ':'

		if parts['shortname']:
			new_name += parts['shortname']

		if parts['icons']:
			new_name += ' ' + parts['icons']

	return new_name


# Returns an array of the values for the given property from xprop.  This
# requires xorg-xprop to be installed.
def xprop(win_id, property):
	try:
		prop = proc.check_output(['xprop', '-id', str(win_id), property], stderr=proc.DEVNULL)
		prop = prop.decode('utf-8')
		print(re.findall('"([^"]+)"', prop))
		return re.findall('"([^"]+)"', prop)

	except proc.CalledProcessError:
		print("Unable to get property for window '%d'" % win_id)
		return None


def icon_for_window(window):
	classes = xprop(window.window, 'WM_CLASS')
	if classes is not None and len(classes) > 0:
		for cls in classes:
			cls = cls.lower()  # case-insensitive matching
			if cls in WINDOW_ICONS:
				return WINDOW_ICONS[cls]

		print('No icon available for: %s' % str(classes))

	return DEFAULT_ICON


# renames all workspaces based on the windows present
def rename_workspaces(i3):
	for workspace in i3.get_tree().workspaces():
		if '' not in workspace.name and '' not in workspace.name and '' not in workspace.name:
			name_parts = parse_workspace_name(workspace.name)
			name_parts['icons'] = ' '.join([icon_for_window(w) for w in workspace.leaves()])
			new_name = construct_workspace_name(name_parts)
			i3.command('rename workspace "%s" to "%s"' % (workspace.name, new_name))


# rename workspaces to just numbers and shortnames.
# called on exit to indicate that this script is no longer running.
def undo_window_renaming(i3):
	for workspace in i3.get_tree().workspaces():
		name_parts = parse_workspace_name(workspace.name)
		name_parts['icons'] = None
		new_name = construct_workspace_name(name_parts)
		i3.command('rename workspace "%s" to "%s"' % (workspace.name, new_name))

	i3.main_quit()
	sys.exit(0)


if __name__ == '__main__':
	i3 = i3ipc.Connection()

	# exit gracefully when ctrl+c is pressed
	for sig in [signal.SIGINT, signal.SIGTERM]:
		signal.signal(sig, lambda signal, frame: undo_window_renaming(i3))

	# call rename_workspaces() for relevant window events
	def window_event_handler(i3, e):
		if e.change in ['new', 'close', 'move']:
			rename_workspaces(i3)

	i3.on('window', window_event_handler)
	rename_workspaces(i3)
	i3.main()
