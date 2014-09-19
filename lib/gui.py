# -*- coding: utf-8 -*-
import xbmc, xbmcgui, time, urllib
import util
import pushhandler
import PushbulletTargets
import devices
import maps
import YDStreamExtractor as StreamExtractor 

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
		BaseWindow.__init__(self,*args,**kwargs)
		
	def onInit(self):
		BaseWindow.onInit(self)
		self._winID = xbmcgui.getCurrentWindowId()
		self.pushList = self.getControl(101)
		token = util.getSetting('token')
		if not token: return
		
		loadVideoThunmbs = util.getSetting('load_video_thumbs',False)
		kodiDevice = devices.getDefaultKodiDevice()
		if not kodiDevice: return
		self.pushList.reset()
		self.pushes = []
		pushes = self.client.pushes()
		if not pushes: return
		items = []
		for push in pushes:
			if  push.get('target_device_iden') == kodiDevice.ID:
				self.pushes.append(push)
				item = xbmcgui.ListItem(push.get('title',push.get('name',push.get('file_name','?'))),iconImage='service-pushbullet-com-{0}.png'.format(push.get('type','')))
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
				item.setProperty('info',push.get('url',push.get('file_url','')))
				item.setProperty('sender',push.get('sender_email',''))
				bg = push.get('image_url','')
				if push.get('type') == 'address':
					bg = maps.Maps().getMap(urllib.quote(push.get('address','')),'None',marker=True,return_url_only=True)
				elif push.get('type') == 'link' and loadVideoThunmbs:
					url = push.get('url')
					if StreamExtractor.mightHaveVideo(url):
						bg = StreamExtractor.getVideoInfo(url).selectedStream().get('thumbnail','')
				item.setProperty('background',bg)
				item.setProperty('date',time.strftime('%m-%d-%Y %H:%M',time.localtime(push.get('created',0))))
				items.append(item)
		self.setProperty('loading','0')
		self.pushList.addItems(items)
		if items: self.setFocusId(101)
		self.reSelect()

	def onClick(self,controlID):
		if controlID == 101:
			idx = self.pushList.getSelectedPosition()
			if idx < 0: return
			if not pushhandler.handlePush(self.pushes[idx],from_gui=True):
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
		if selected < 0: return
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
		options = ['Delete']
		idx = xbmcgui.Dialog().select('Options',options)
		if idx < 0: return
		if idx == 0:
			self.client.deletePush(self.pushes[selected])

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
		self.getControl(101).reset()
		items = []
		for i in self.data.get('items',[]):
			item = xbmcgui.ListItem(i.get('text'))
			item.setProperty('checked',i.get('checked') and '1' or '') 
			items.append(item)
		self.getControl(101).addItems(items)
		if items: self.setFocusId(101)

	def onClick(self,controlID):
		if controlID == 101:
			idx = self.getControl(101).getSelectedPosition()
			if idx < 0: return
			item = self.getControl(101).getListItem(idx)
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
	