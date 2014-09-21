# -*- coding: utf-8 -*-
import xbmc, xbmcgui
import YDStreamExtractor as StreamExtractor
import YDStreamUtils as StreamUtils
import util

def getURLMediaType(url):
	videoTypes = xbmc.getSupportedMedia('video')
	musicTypes = xbmc.getSupportedMedia('music')
	imageTypes = xbmc.getSupportedMedia('picture')
	ext = url.rsplit('.',1)[-1]
	if ext in videoTypes:
		return 'video'
	elif ext in musicTypes:
		return 'music'
	elif ext in imageTypes:
		return 'image'
	return None

def canHandle(data):
	if data.get('type') == 'link':
		url = data.get('url','')
		if StreamExtractor.mightHaveVideo(url): return True
		return bool(getURLMediaType(url))
	elif data.get('type') == 'file':
		return data.get('file_type','').startswith('image/') or data.get('file_type','').startswith('audio/') or data.get('file_type','').startswith('video/')
	elif data.get('type') == 'note':
		return True
	elif data.get('type') == 'list':
		return True
	elif data.get('type') == 'address':
		return True
	return False

def checkForWindow():
	if not xbmc.getCondVisibility('IsEmpty(Window.Property(pushbullet))'):
		xbmc.executebuiltin('Action(info)')
		return True

def handlePush(data,from_gui=False):
	if not from_gui and checkForWindow(): #Do nothing if the window is open
		return False
	if data.get('type') == 'link':
		url = data.get('url','')
		if StreamExtractor.mightHaveVideo(url):
			vid = StreamExtractor.getVideoInfo(url)
			if vid:
				if vid.hasMultipleStreams():
					vlist = []
					for info in vid.streams():
						vlist.append(info['title'] or '?')
					idx = xbmcgui.Dialog().select('Select Video',vlist)
					if idx < 0: return
					vid.selectStream(idx)
				util.LOG(vid.streamURL()) #TODO: REMOVE
				StreamUtils.play(vid.streamURL())
				return True
		media = getURLMediaType(url)
		if media == 'video' or media == 'music':
			StreamUtils.play(url)
			return True
		elif media == 'image':
			import gui
			gui.showImage(url)
			return True
	elif data.get('type') == 'file':
		if data.get('file_type','').startswith('image/'):
			import gui
			gui.showImage(data.get('file_url',''))
			return True
		elif data.get('file_type','').startswith('video/') or data.get('file_type','').startswith('audio/'):
			StreamUtils.play(data.get('file_url',''))
			return True
	elif data.get('type') == 'note':
		import gui
		gui.showNote(data.get('body',''))
		return True
	elif data.get('type') == 'list':
		import gui
		gui.showList(data)
		return True
	elif data.get('type') == 'address':
		import urllib
		xbmc.executebuiltin('XBMC.RunScript(special://home/addons/service.pushbullet.com/lib/maps.py,service.pushbullet.com,%s,None,)' % urllib.quote(data.get('address','')))
		return True

	return False
	
	'''{u'iden': u'ujxCHwc6fiSsjAl11HK7y0',
		u'created': 1411009240.141888,
		u'receiver_email': u'ruuk25@gmail.com',
		u'items': [],
		u'target_device_iden': u'ujxCHwc6fiSsjz477zOU0a',
		u'file_url': u'https://s3.amazonaws.com/pushbullet-uploads/ujxCHwc6fiS-wnH7qXNVOruppCCglRlC6iUXWHWR5xEV/IMG_20140827_164312.jpg',
		u'modified': 1411009240.149686, u'dismissed': False,
		u'sender_email_normalized': u'ruuk25@gmail.com',
		u'file_type': u'image/jpeg',
		u'image_url': u'https://pushbullet.imgix.net/ujxCHwc6fiS-wnH7qXNVOruppCCglRlC6iUXWHWR5xEV/IMG_20140827_164312.jpg',
		u'sender_email': u'ruuk25@gmail.com',
		u'file_name': u'IMG_20140827_164312.jpg',
		u'active': True,
		u'receiver_iden': u'ujxCHwc6fiS',
		u'sender_iden': u'ujxCHwc6fiS',
		u'type': u'file',
		u'receiver_email_normalized': u'ruuk25@gmail.com'}'''

#def _getVideoThumb(url,item):
#	info = StreamExtractor.getVideoInfo(url)
#	item.setProperty('background',info.thumbnail)
#
#def getVideoThumbnails(items):
#	import threadpool
#	pool = threadpool.ThreadPool(3)
#	reqs = threadpool.makeRequests(_getVideoThumb, items)
#	[pool.putRequest(req) for req in reqs]
#	pool.wait(return_results=True)
#	pool.dismissWorkers()
