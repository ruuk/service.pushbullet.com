# -*- coding: utf-8 -*-
import sys
from lib import util

def showError(msg):
	import xbmcgui
	xbmcgui.Dialog().ok('ERROR', 'Error:','',msg)
	
def loadTokenFromFile():
	import OAuthHelper
	
	token = OAuthHelper.getToken('service.pushbullet.com',from_file=True)
	if token: saveToken(token)

def deviceNameExists(client,name):
	from lib import PushbulletTargets
	try:
		for d in client.getDevicesList():
			if not d.get('active'): continue
			if name == d.get('nickname'): return True
		return False
	except PushbulletTargets.PushbulletException, e:
		showError(e.message)
		return None
	
def addNewDevice(client,device):
	import xbmcgui
	from lib import PushbulletTargets
	
	#TODO: Check for existing device nickname and handle	
	
	device.name = xbmcgui.Dialog().input('Enter a name for this device:',device.name or 'Kodi Device') or device.name
	if not device.name: return False
	
	while deviceNameExists(client,device.name):
		device.name = xbmcgui.Dialog().input('Device already exists. Try again.',device.name or '')
		if not device.name: return
		
	try:
		client.addDevice(device)
	except PushbulletTargets.PushbulletException, e:
		util.LOG('FAILED TO ADD DEVICE: {0}'.format(device.name))
		showError(e.message)
		return False
	return True
	
def linkDevice():
	import xbmcgui
	from lib import PushbulletTargets
	from lib import devices
	
	token = util.getSetting('token')
	
	if not token:
		xbmcgui.Dialog().ok('No Token', 'User token not set.','Please set the token and try again')
		return
		
	client = PushbulletTargets.Client(token)
	deviceMap = {}
	try:
		for d in client.getDevicesList():
			if not d.get('active'): continue
			deviceMap[d['iden']] = d['nickname']
	except PushbulletTargets.PushbulletException, e:
		showError(e.message)
		return
	
	idx = xbmcgui.Dialog().select('Choose Device',deviceMap.values() + ['+ Add As New'])
	if idx < 0: return
	
	dev = devices.KodiDevice(None,util.getSetting('device_name') or None)
	if idx == len(deviceMap):
		if not addNewDevice(client,dev): return
	else:
		dev.ID = deviceMap.keys()[idx]
		dev.name = deviceMap.values()[idx] or dev.name
		
	util.setSetting('device_iden',dev.ID)
	util.setSetting('device_name',dev.name)
	util.LOG('DEVICE LINKED: {0}'.format(dev.name))
	xbmcgui.Dialog().ok('Linked', 'This Kodi device: ', '  [B]{0}[/B]'.format(dev.name), 'is ready to receive push notices.')

def renameDevice():
	import xbmcgui
	from lib import devices
	from lib import PushbulletTargets
	from lib import util
	
	dev = devices.getDefaultKodiDevice()
	if not dev.ID:
		xbmcgui.Dialog().ok('Not Linked','This device is not yet linked.')
	name = xbmcgui.Dialog().input('Enter a new name for this device:',dev.name or '')
	if not name: return
	if name == dev.name: return
	
	token = util.getSetting('token')
	
	client = PushbulletTargets.Client(token)
	
	while deviceNameExists(client,name):
		name = xbmcgui.Dialog().input('Device already exists. Try again.',dev.name or '')
		if not name: return
		if name == dev.name: return

	if not token:
		xbmcgui.Dialog().ok('No Token', 'User token not set.','Please set the token and try again')
		return
		
	try:
		if client.updateDevice(dev,nickname=name):
			util.setSetting('device_name',dev.name)
			xbmcgui.Dialog().ok('Done','Device renamed to: ','',dev.name)
			
	except PushbulletTargets.PushbulletException, e:
		showError(e.message)

def selectDevice():
	from lib import gui, PushbulletTargets

	token = util.getSetting('token')

	client = PushbulletTargets.Client(token)

	ID = gui.selectDevice(client,extra='None')
	if ID == None: return
	util.setSetting('selected_device',ID)

def saveToken(token):
	util.setSetting('token',token)

def authorize():
	import OAuthHelper
	
	token = OAuthHelper.getToken('service.pushbullet.com')
	if token: saveToken(token)

def main():
	if not util.getToken():
		import xbmcgui
		xbmcgui.Dialog().ok('Needs Setup','Please open the addon settings, ','authorize the addon and add this device.')
		util.ADDON.openSettings()
		return
		
	if not util.getSetting('device_iden'):
		import xbmcgui
		xbmcgui.Dialog().ok('Needs Setup','This device still needs to be added.','Please open the addon settings, ','and add this device.')
		util.ADDON.openSettings()
		return

	from lib import gui
	gui.start()

def handleArg(arg):
	if arg == 'LINK_DEVICE':
		linkDevice()
	elif arg == 'RENAME_DEVICE':
		renameDevice()
	elif arg == 'TOKEN_FROM_FILE':
		loadTokenFromFile()
	elif arg == 'SELECT_DEVICE':
		selectDevice()
	elif arg == 'AUTHORIZE':
		authorize()

if __name__ == '__main__':
	try:
		args = None
		if len(sys.argv) > 1:
			args = sys.argv[1:]
		
		if args:
			handleArg(args[0])
		else:
			main()
	except:
		import traceback
		traceback.print_exc()