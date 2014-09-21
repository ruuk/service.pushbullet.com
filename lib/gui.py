# -*- coding: utf-8 -*-
import xbmc, xbmcgui, time, urllib, os
import util
import pushhandler
import PushbulletTargets
import devices
import maps
import YDStreamExtractor as StreamExtractor 

CACHE_PATH = os.path.join(xbmc.translatePath(util.ADDON.getAddonInfo('profile')),'cache')
if not os.path.exists(CACHE_PATH): os.makedirs(CACHE_PATH)

def getCachedData(ID):
	path = os.path.join(CACHE_PATH,ID)
	if os.path.exists(path):
		with open(path,'r') as f: return f.read()
	return None

def cacheData(ID,data):
	path = os.path.join(CACHE_PATH,ID)
	with open(path,'w') as f: f.write(data)

def deleteCachedData(ID):
	path = os.path.join(CACHE_PATH,ID)
	if os.path.exists(path): os.remove(path)

def cleanCache(used_ids):
	for ID in os.listdir(CACHE_PATH):
		if not ID in used_ids: deleteCachedData(ID)

class BaseWindow(xbmcgui.WindowXML):
	def __init__(self,*args,**kwargs):
		self._closing = False
		self._winID = ''

	def onInit(self):
		self._winID = xbmcgui.getCurrentWindowId()
		
	def setProperty(self,key,value):
		if self._closing: return
		xbmcgui.Window(self._winID).setProperty(key,value)
		xbmcgui.WindowXMLDialog.setProperty(self,key,value)
		
	def doClose(self):
		self._closing = True
		self.close()

class PushbulletWindow(BaseWindow):
	def __init__(self,*args,**kwargs):
		self.client = PushbulletTargets.Client(util.getToken())
		self.lastSelected = None
		self.pushes = []
		BaseWindow.__init__(self,*args,**kwargs)
		
	def onInit(self):
		BaseWindow.onInit(self)
		self.setProperty('loading','1')
		self._winID = xbmcgui.getCurrentWindowId()
		self.pushList = self.getControl(101)
		token = util.getSetting('token')
		if not token: return
		
		loadVideoThumbs = util.getSetting('load_video_thumbs',False)
		kodiDevice = devices.getDefaultKodiDevice()
		if not kodiDevice: return
		self.pushes = []
		pushes = self.client.pushes()
		if not pushes: return
		items = []
		IDs = []
		
		for push in pushes:
			if not push.get('target_device_iden') == kodiDevice.ID: continue
		
			self.pushes.append(push)

			iden = push.get('iden')
			IDs.append(iden)

			title = push.get('title',push.get('name',push.get('file_name','')))
			bg = push.get('image_url','')
			info = push.get('url','')
			mediaIcon = ''
			media = ''

			if push.get('type') == 'address':
				bg = maps.Maps().getMap(urllib.quote(push.get('address','')),'None',marker=True,return_url_only=True)
			elif push.get('type') == 'link':
				url = push.get('url')
				if StreamExtractor.mightHaveVideo(url):
					media = 'video'
					if loadVideoThumbs:
						bg = getCachedData(iden)
						if not bg:
							bg = StreamExtractor.getVideoInfo(url).thumbnail
							cacheData(iden,bg)
				else:
					media = pushhandler.getURLMediaType(url)
				if not title:
					title = url.rsplit('/',1)[-1]
			elif push.get('type') == 'file':
				info = urllib.unquote(push.get('file_url',''))
				if push.get('file_type','').startswith('image/'):
					media = 'image'
				elif push.get('file_type','').startswith('audio/'):
					media = 'music'
				elif push.get('file_type','').startswith('video/'):
					media = 'video'
			if media:
				mediaIcon = 'service-pushbullet-com-icon_{0}.png'.format(media)

			item = xbmcgui.ListItem(title,iconImage='service-pushbullet-com-{0}.png'.format(push.get('type','')))

			desc = push.get('body',push.get('address',''))
			if push.get('type') == 'list':
				li = []
				ct = 0
				for i in push.get('items',[]):
					li.append(i.get('text',''))
					ct+=1
					if ct > 50: break
				desc = ', '.join(li)
			desc = '[CR]'.join(desc.splitlines()[:4])
			item.setProperty('description',desc)
			item.setProperty('info',info)
			item.setProperty('sender',push.get('sender_email',''))
			item.setProperty('media_icon',mediaIcon)
			item.setProperty('background',bg)
			item.setProperty('date',time.strftime('%m-%d-%Y %H:%M',time.localtime(push.get('created',0))))
			items.append(item)

		self.setProperty('loading','0')
		self.pushList.reset()
		self.pushList.addItems(items)

		if items: self.setFocusId(101)
		self.reSelect()
		cleanCache(IDs)

	def onClick(self,controlID):
		if controlID == 101:
			push = self.getSelectedPush()
			if not push: return
			if not pushhandler.handlePush(push,from_gui=True):
				xbmcgui.Dialog().ok('Sorry','Sorry:','','No handler for this type of push.')

	def onAction(self,action):
		try:
			if action.getId() == 11: #xbmcgui.ACTION_SHOW_INFO:
				self.onInit()
			elif action.getId() == 117: #xbmcgui.ACTION_CONTEXT_MENU:
				self.doMenu()
			push = self.getSelectedPush()
			if push: self.lastSelected = push.get('iden')
		except:
			import traceback
			xbmc.log(traceback.format_exc())
		finally:
			BaseWindow.onAction(self,action)
		
	def getSelectedPush(self):
		selected = self.pushList.getSelectedPosition()
		if selected < 0 or selected >= len(self.pushes): return
		return self.pushes[selected]

	def reSelect(self):
		if not self.lastSelected: return
		idx = next((i for i in range(len(self.pushes)) if self.pushes[i].get('iden') == self.lastSelected),-1)
		if idx < 0:
			self.lastSelected = None
		else:
			self.getControl(101).selectItem(idx)

	def doMenu(self):
		selected = self.pushList.getSelectedPosition()
		if selected < 0: return
		options = []
		push = self.pushes[selected]
		if push.get('type') in ('file','link'):
			options.append(('download','Download'))
		options.append(('delete','Delete'))
		idx = xbmcgui.Dialog().select('Options',[o[1] for o in options])
		if idx < 0: return
		choice = options[idx][0]
		
		if choice == 'download':
			import os
			d = util.Downloader()
			targetDir = os.path.join(xbmc.translatePath(util.ADDON.getAddonInfo('profile')),'temp')
			if not os.path.exists(targetDir): os.makedirs(targetDir)
			finalTargetDir = d.chooseDirectory()
			if not finalTargetDir: return
			url = push.get('type') == 'file' and push.get('file_url') or push.get('url')
			d.downloadURL(targetDir,url,fname=push.get('file_name'),final_target_dir=finalTargetDir)
		elif choice == 'delete':
			#set last selected to the item above, or the item below if we are at the top
			closest = selected - 1
			if closest < 0: closest = self.getControl(101).size() - 1
			self.lastSelected = self.pushes[closest].get('iden')
			self.pushes[selected]
			
			self.client.deletePush(push)
			self.onInit()

class ImageViewWindow(BaseWindow):
	def __init__(self,*args,**kwargs):
		self.url = kwargs.get('url','')
		BaseWindow.__init__(self,*args,**kwargs)

	def onInit(self):
		BaseWindow.onInit(self)
		self.setProperty('image_url',self.url)

class NoteViewWindow(BaseWindow):
	def __init__(self,*args,**kwargs):
		self.text = kwargs.get('text','')
		BaseWindow.__init__(self,*args,**kwargs)

	def onInit(self):
		BaseWindow.onInit(self)
		self.getControl(100).setText(self.text)
		import xbmc
		xbmc.sleep(100) #Attempt to give scrollbar time to becomve visible so we can focus it
		if xbmc.getCondVisibility('Control.IsVisible(101)'): self.setFocusId(101) #Prevent log message by checking visibility first

class ListViewWindow(BaseWindow):
	def __init__(self,*args,**kwargs):
		self.data = kwargs.get('data','')
		self.client = PushbulletTargets.Client(util.getToken())
		BaseWindow.__init__(self,*args,**kwargs)

	def onInit(self):
		BaseWindow.onInit(self)
		self.listControl = self.getControl(101)
		items = []
		for i in self.data.get('items',[]):
			item = xbmcgui.ListItem(i.get('text'))
			item.setProperty('checked',i.get('checked') and '1' or '') 
			items.append(item)
		self.listControl.reset()
		self.listControl.addItems(items)
		if items: self.setFocusId(101)

	def refresh(self):
		idx = self.listControl.getSelectedPosition()
		for p in self.client.pushes():
			if p.get('iden') == self.data.get('iden'):
				self.data = p
				break

		self.onInit()
		if idx < 0 or idx >= self.listControl.size(): return
		self.listControl.selectItem(idx)

	def onAction(self,action):
		try:
			if action.getId() == 11: #xbmcgui.ACTION_SHOW_INFO:
				self.refresh()
		finally:
			BaseWindow.onAction(self,action)

	def onClick(self,controlID):
		if controlID == 101:
			idx = self.listControl.getSelectedPosition()
			if idx < 0: return
			item = self.listControl.getListItem(idx)
			checked = not self.data['items'][idx].get('checked')
			self.data['items'][idx]['checked'] = checked
			item.setProperty('checked',checked and '1' or '')
			self.client.modifyPush(self.data)
			

		
def showImage(url):
	w = ImageViewWindow('service.pushbullet.com-image.xml',util.ADDON.getAddonInfo('path'),'Main','720p',url=url)
	w.doModal()
	del w

def showNote(text):
	w = NoteViewWindow('service.pushbullet.com-note.xml',util.ADDON.getAddonInfo('path'),'Main','720p',text=text)
	w.doModal()
	del w

def showList(data):
	w = ListViewWindow('service.pushbullet.com-list.xml',util.ADDON.getAddonInfo('path'),'Main','720p',data=data)
	w.doModal()
	del w

def start():
	w = PushbulletWindow('service.pushbullet.com-pushes.xml',util.ADDON.getAddonInfo('path'),'Main','720p')
	w.doModal()
	del w

		