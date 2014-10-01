# -*- coding: utf-8 -*-
import sys, time
import xbmc
from lib import util, pushhandler
from lib import PushbulletTargets
PushbulletTargets.LOG = util.LOG

from lib import devices
import YDStreamUtils as StreamUtils

def ERROR():
	import traceback
	xbmc.log(traceback.format_exc())

class TargetsBox(object):
	def __init__(self):
		self.token = util.getSetting('token')
		self.deviceID = util.getSetting('device_iden')
		self.deviceName = util.getSetting('device_name')
		self.device = None
		self.targets = None

		self.reconnectDelay = 5
		self.nextReconnect = 0
		self.hasConnected = False
		self.badToken = False
		self.start()
		self.connect()

	def start(self):
		self.targets = PushbulletTargets.Targets(
			self.token,
			most_recent=util.getSetting('most_recent',0),
			most_recent_callback=self.mostRecentUpdated
		)

		self.device = devices.getDefaultKodiDevice(self.deviceID,self.deviceName)
		self.targets.registerDevice(self.device)

	def ready(self):
		if self.badToken: return False
		if self.hasConnected:
			return not self.badToken and not self.targets.terminated and self.readyToReconnect()
		else:
			if not self.readyToReconnect(): return False
			self.connect()

	def join(self,timeout=0.2):
		self.targets._th.join(timeout=timeout)

	def mostRecentUpdated(self,modified):
		util.setSetting('most_recent','{0:10f}'.format(modified))

	def close(self):
		try:
			self.targets.close(force=True)
			self.targets._th.join()
		except RuntimeError:
			pass

	def updateReconnectDelay(self):
		if self.reconnectDelay > 60: return
		self.reconnectDelay *= 2

	def readyToReconnect(self):
		return time.time() > self.nextReconnect

	def connect(self):
		try:
			self.targets.connect()
			self.hasConnected = True
			self.badToken = False
			self.reconnectDelay = 5
		except PushbulletTargets.ws4py.exc.HandshakeError, e:
			self.badToken = True
			if '401' in e.msg:
				util.LOG('CONNECT HANDSHAKE ERROR - BAD TOKEN')
			else:
				ERROR('CONNECT HANDSHAKE ERROR')
			return
		except:
			ERROR()
			self.nextReconnect = time.time() + self.reconnectDelay
			util.LOG('CONNECT ERROR: Waiting {0} seconds'.format(self.reconnectDelay))
			self.updateReconnectDelay()
			return

class PushbulletService(xbmc.Monitor):
	def __init__(self):
		self.targetsBox = None
		self.start()

	def onAbortRequested(self):
		if not self.targetsBox: return
		self.targetsBox.close()

	def onSettingsChanged(self):
		self.loadSettings()

	def credentialsUpdated(self):
		token = util.getSetting('token')
		deviceID = util.getSetting('device_iden')
		if not self.targetsBox:
			if token and deviceID:
				return True
			else:
				return None
		if token != self.targetsBox.token:
			util.LOG('TOKEN CHANGED')
			return True

		if deviceID != self.targetsBox.deviceID:
			util.LOG('DEVICE CHANGED FROM: {0} TO: {1}'.format(self.targetsBox.deviceName,util.getSetting('device_name')))
			return True

		return False
		
	def loadSettings(self):
		self.reconnectDelay = 5
		self.interruptMedia = util.getSetting('interrupt_media',False)
		self.instantPlay = util.getSetting('instant_play',True)
		self.showNotification = util.getSetting('show_notification',True)
		
		if self.credentialsUpdated():
			if self.targetsBox: self.targetsBox.close()
			self.targetsBox = TargetsBox()

	def start(self):
		util.LOG('SERVICE: STARTED {0}'.format(util.ADDON.getAddonInfo('version')))
		
		self.loadSettings()
		
		while not xbmc.abortRequested:
			if self.targetsBox and self.targetsBox.ready():
				self.active()
			else:
				self.idle()
		self.done()
		
	def runServer(self):
		while self.targetsBox.ready() and not xbmc.abortRequested:
			self.targetsBox.join()
			if self.targetsBox.device.hasPush():
				if self.instantPlay:
					if not StreamUtils.isPlaying() or self.interruptMedia:
						data = self.targetsBox.device.getNext()
						if data: pushhandler.handlePush(data)
				else:
					if self.showNotification:
						data = self.targetsBox.device.getNext()
						if data:
							util.notify(
								'{0}: {1}'.format(util.T(32090),data.get('type','?')),
								data.get('title','')
							)
					self.targetsBox.device.clear()

			xbmc.sleep(200)
		
		self.targetsBox.close()
		self.targetsBox = None

	def active(self):
		util.LOG('SERVICE: ACTIVE')
				
		try:
			self.runServer()
		except:
			util.ERROR('Server Error')
			util.notify(util.T(32105),util.T(32106))
			xbmc.sleep(5000)

		if not xbmc.abortRequested: #If not shutting down, reset in case we died of error
			self.loadSettings()
		
	def idle(self):
		util.LOG('SERVICE: IDLING')
		while not (self.targetsBox and self.targetsBox.ready()) and not xbmc.abortRequested:
			xbmc.sleep(1000)

	def done(self):
		util.LOG('SERVICE: DONE')

if __name__ == '__main__':
	if sys.argv[0] == 'service.pushbullet.com' and len(sys.argv) < 2:
		import main
		main.main()
	else:
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
