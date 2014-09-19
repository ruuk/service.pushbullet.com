# -*- coding: utf-8 -*-
import Queue
import PushbulletTargets
import util
import pushhandler

class KodiDevice(PushbulletTargets.Device):
	def init(self):
		self.queue = Queue.Queue()

	def clear(self):
		push = True
		while push: push = self.getNext()

	def hasPush(self):
		return not self.queue.empty()

	def getNext(self):
		if self.queue.empty(): return None
		try:
			data = self.queue.get_nowait()
			self.queue.task_done()
			return data
		except Queue.Empty:
			pass
		return None

	def link(self,data):
		if not pushhandler.canHandle(data):
			pushhandler.checkForWindow()
			return

		self.queue.put_nowait(data)
		return False

	def file(self,data):
		if not pushhandler.canHandle(data):
			pushhandler.checkForWindow()
			return

		self.queue.put_nowait(data)
		return False

	def note(self,data):
		if not pushhandler.canHandle(data):
			pushhandler.checkForWindow()
			return

		self.queue.put_nowait(data)
		return False

	def list(self,data):
		if not pushhandler.canHandle(data):
			pushhandler.checkForWindow()
			return

		self.queue.put_nowait(data)
		return False
	
	def address(self,data):
		if not pushhandler.canHandle(data):
			pushhandler.checkForWindow()
			return

		self.queue.put_nowait(data)
		return False

def getDefaultKodiDevice(device=None):
	ID = util.getSetting('device_iden')
	if not ID: return None
	if device and device.ID == ID: return device
	name = util.getSetting('device_name')
	return KodiDevice(ID,name)