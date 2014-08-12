# -*- coding: utf-8 -*-
import xbmc, xbmcgui
from lib import util

from lib import PushbulletTargets
PushbulletTargets.LOG = util.LOG

from lib import devices
import YDStreamExtractor as StreamExtractor
import YDStreamUtils as StreamUtils

def handlePush(data):
	if data.get('type') == 'link':
		url = data.get('url','')
		if StreamExtractor.mightHaveVideo(url):
			vid = StreamExtractor.getVideoInfo(url)
			if vid.hasMultipleStreams():
				vlist = []
				for info in vid.streams():
					vlist.append(info['title'] or '?')
				idx = xbmcgui.Dialog().select('Select Video',vlist)
				if idx < 0: return
				vid.selectStream(idx)
			util.LOG(vid.streamURL()) #TODO: REMOVE
			StreamUtils.play(vid.streamURL())
		
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
		self.token = util.getSetting('token')
		self.device = devices.getDefaultKodiDevice()

		self.isActive = self.token and self.device.isValid()
		if self.isActive:
			if not self.targets or self.token != oldToken:
				self.setTargets()
			elif self.targets and self.device != oldDevice:
				self.targets.unregisterDevice(oldDevice)
				self.targets.registerDevice(self.device)
				util.LOG('DEVICE CHANGED FROM: {0} TO: {1}'.format(oldDevice.name,self.device.name))

	def setTargets(self):
		old = self.targets
		self.targets = PushbulletTargets.Targets(self.token)
		self.targets.registerDevice(self.device)
		self.targets.connect()
		if old:
			util.LOG('TOKEN CHANGED - TARGETS RESET')
			old.close(force=True)

	def start(self):
		util.LOG('SERVICE: STARTED')
		
		self.loadSettings()
		
		while not xbmc.abortRequested:
			if self.isActive:
				self.active()
			else:
				self.idle()
		self.done()
		
	def active(self):
		util.LOG('SERVICE: ACTIVE')
					
		while self.isActive and not self.targets.terminated and not xbmc.abortRequested:
			self.targets._th.join(timeout=0.2)
			data = self.device.getNext()
			if data: handlePush(data)
			xbmc.sleep(200)

		self.targets.close(force=True)
		self.targets = None
	
	def idle(self):
		util.LOG('SERVICE: IDLING')
		while not self.isActive and not xbmc.abortRequested: xbmc.sleep(1000)

	def done(self):
		util.LOG('SERVICE: DONE')
		
if __name__ == '__main__':
	PushbulletService()
