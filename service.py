# -*- coding: utf-8 -*-
import sys
import xbmc, xbmcgui
from lib import util, pushhandler

from lib import PushbulletTargets
PushbulletTargets.LOG = util.LOG

from lib import devices
import YDStreamUtils as StreamUtils

def ERROR():
	import traceback
	xbmc.log(traceback.format_exc())

class PushbulletService(xbmc.Monitor):
	def __init__(self):
		self.isActive = False
		self.targets = None
		self.token = None
		self.device = None
		self.start()

	def onAbortRequested(self):
		if not self.targets: return
		self.targets.close(force=True)

	def onSettingsChanged(self):
		self.loadSettings()

	def loadSettings(self):
		oldToken = self.token
		oldDevice = self.device
		self.interruptMedia = util.getSetting('interrupt_media',False)
		self.instantPlay = util.getSetting('instant_play',True)
		self.showNotification = util.getSetting('show_notification',True)
		self.token = util.getSetting('token')
		self.device = devices.getDefaultKodiDevice(self.device)

		self.isActive = self.token and self.device and self.device.isValid()
		if self.isActive:
			if not self.targets or self.token != oldToken:
				self.setTargets(oldToken)
			elif self.targets and self.device != oldDevice:
				self.targets.unregisterDevice(oldDevice)
				self.targets.registerDevice(self.device)
				util.LOG('DEVICE CHANGED FROM: {0} TO: {1}'.format(oldDevice.name,self.device.name))

	def mostRecentUpdated(self,modified):
		util.setSetting('most_recent','{0:10f}'.format(modified))

	def setTargets(self,oldToken):
		old = self.targets
		
		targets = PushbulletTargets.Targets(
			self.token,
			most_recent=util.getSetting('most_recent',0),
			most_recent_callback=self.mostRecentUpdated
		)
		
		targets.registerDevice(self.device)
		try:
			targets.connect()
		except:
			ERROR()
			self.token = oldToken
			if self.targets: self.targets.registerDevice(self.device)
			self.isActive = self.token and self.device.isValid()
			util.LOG('CONNECT ERROR - REVERTING TOKEN')
			return

		self.targets = targets

		if old:
			util.LOG('TOKEN CHANGED - TARGETS RESET')
			old.close(force=True)

	def start(self):
		util.LOG('SERVICE: STARTED')
		
		self.loadSettings()
		
		while not xbmc.abortRequested:
			if self.targets and self.isActive:
				self.active()
			else:
				self.idle()
		self.done()
		
	def active(self):
		util.LOG('SERVICE: ACTIVE')
					
		while self.isActive and not self.targets.terminated and not xbmc.abortRequested:
			self.targets._th.join(timeout=0.2)
			if self.device.hasPush():
				if self.instantPlay:
					if not StreamUtils.isPlaying() or self.interruptMedia:
						data = self.device.getNext()
						if data: pushhandler.handlePush(data)
				else:
					if self.showNotification:
						data = self.device.getNext()
						if data:
							xbmcgui.Dialog().notification(
								'New Push: {0}'.format(data.get('type','?')),
								data.get('title',''),
								util.ADDON.getAddonInfo('icon'),
								5000
							)
					self.device.clear()

			xbmc.sleep(200)

		self.targets.close(force=True)
		self.targets = None
	
	def idle(self):
		util.LOG('SERVICE: IDLING')
		while not self.isActive and not xbmc.abortRequested: xbmc.sleep(1000)

	def done(self):
		util.LOG('SERVICE: DONE')

if __name__ == '__main__':
	try:
		args = None
		if len(sys.argv) > 1:
			args = sys.argv[1:]
		
		if args:
			import main
			main.handleArg(args[0])
		else:
			PushbulletService()
	except:
		import traceback
		traceback.print_exc()
