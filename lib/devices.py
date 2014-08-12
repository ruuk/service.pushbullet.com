# -*- coding: utf-8 -*-
import Queue
import PushbulletTargets
import YDStreamExtractor as StreamExtractor
import util

class KodiDevice(PushbulletTargets.Device):
	def init(self):
		self.queue = Queue.Queue()

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
		url = data.get('url','')
		#title = data.get('title','')
		#message = data.get('body','')
		if not StreamExtractor.mightHaveVideo(url): return True
		self.queue.put_nowait(data)
		return True
		
def getDefaultKodiDevice():
	ID = util.getSetting('device_iden')
	name = util.getSetting('device_name')
	return KodiDevice(ID,name)