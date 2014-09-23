# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcaddon, xbmcvfs
import urllib2, urlparse, traceback, os

ADDON = xbmcaddon.Addon()

def LOG(msg):
	 xbmc.log('service.pushbullet.com: {0}'.format(msg))
	
def ERROR(msg):
	LOG('ERROR: {0}').format(msg)
	xbmc.log(traceback.format_exc())

def getSetting(key,default=None):
	val = ADDON.getSetting(key)
	if val == '': return default
	if isinstance(default,bool):
		return  val == 'true'
	elif isinstance(default,int):
		try:
			return int(val)
		except:
			pass
		try:
			return float(val)
		except:
			return default

	return val

def setSetting(key,value):
	return ADDON.setSetting(key, value)
	
def getToken():
	return getSetting('token')

class Downloader:
	def __init__(self,header='Downloading',message=''):
		self.message = message
		self.prog = xbmcgui.DialogProgress()
		self.prog.create(header,message)
		self.current = 0
		self.display = ''
		self.file_pct = 0
		
	def progCallback(self,read,total):
		if self.prog.iscanceled(): return False
		pct = int(((float(read)/total) * (self.file_pct)) + (self.file_pct * self.current))
		self.prog.update(pct)
		return True
		
	def downloadURLs(self,targetdir,urllist,ext=''):
		file_list = []
		self.total = len(urllist)
		self.file_pct = (100.0/self.total)
		try:
			for url,i in zip(urllist,range(0,self.total)):
				self.current = i
				if self.prog.iscanceled(): break
				self.display = 'File {0} of {1}'.format(i+1,self.total)
				self.prog.update(int((i/float(self.total))*100),self.message,self.display)
				fname = os.path.join(targetdir,str(i) + ext)
				fname, ftype = self.getUrlFile(url,fname,callback=self.progCallback) #@UnusedVariable
				file_list.append(fname)
		except:
			ERROR('DOWNLOAD URLS ERROR')
			self.prog.close()
			return None
		self.prog.close()
		return file_list
	
	def downloadURL(self,targetdir,url,fname=None,final_target_dir=None):
		if not fname:
			fname = os.path.basename(urlparse.urlsplit(url)[2])
			if not fname: fname = 'file'
		f,e = os.path.splitext(fname)
		fn = f
		ct=0
		while ct < 1000:
			ct += 1
			path = os.path.join(targetdir,fn + e)
			finalPath = os.path.join(final_target_dir,fn + e)
			if not xbmcvfs.exists(path): break
			fn = f + str(ct)
		else:
			raise Exception
		
		try:
			self.current = 0
			self.display = 'Downloading {0}'.format(os.path.basename(path))
			self.prog.update(0,self.message,self.display)
			t,ftype = self.getUrlFile(url,path,callback=self.progCallback) #@UnusedVariable
		except:
			ERROR('DOWNLOAD URL ERROR')
			self.prog.close()
			return (None,'')
		finally:
			self.prog.close()
		if final_target_dir:
			xbmcvfs.copy(path,finalPath)
			xbmcvfs.delete(path)
		return (os.path.basename(path),ftype)
		
		
			
	def fakeCallback(self,read,total): return True

	def getUrlFile(self,url,target=None,callback=None,fix_extension=False):
		if not target: return #do something else eventually if we need to
		if not callback: callback = self.fakeCallback
		opener = urllib2.build_opener()
		opener.addheaders = [('User-agent', 'Mozilla/5.0')]
		urlObj = opener.open(url)
		size = int(urlObj.info().get("content-length",-1))
		ftype = urlObj.info().get("content-type",'')
		if fix_extension:
			ext = None
			if '/' in ftype: ext = '.' + ftype.split('/')[-1].replace('jpeg','jpg')
			if ext:
				fname, x = os.path.splitext(target) #@UnusedVariable
				target = fname + ext
		#print urlObj.info()
		#Content-Disposition: attachment; filename=FILENAME
		outfile = open(target, 'wb')
		read = 0
		bs = 1024 * 8
		while 1:
			block = urlObj.read(bs)
			if block == "": break
			read += len(block)
			outfile.write(block)
			if not callback(read, size): raise Exception('Download Canceled')
		outfile.close()
		urlObj.close()
		return (target,ftype)

	def chooseDirectory(self):
		fpath = xbmcgui.Dialog().browseSingle(3,'Choose Directory','files')
		if not fpath: return None
		return fpath

	def youtubeDLDownload(self,vid,path,target=None):
		import YDStreamExtractor as StreamExtractor 
		import YDStreamUtils as StreamUtils	
		if not target: target = self.chooseDirectory()
		if not target: return
		
		with StreamUtils.DownloadProgress() as prog:
			try:
				StreamExtractor.disableDASHVideo(True)
				StreamExtractor.setOutputCallback(prog)
				result = StreamExtractor.downloadVideo(vid,path)
			finally:
				StreamExtractor.setOutputCallback(None)
		if not result and result.status != 'canceled':
				xbmcgui.Dialog().ok('Download Failed','[CR]',result.message)
		elif result:
			xbmcgui.Dialog().ok('Done','Download Complete','[CR]',result.filepath)
		if target:
			xbmcvfs.copy(result.filepath,os.path.join(target,os.path.basename(result.filepath)))
			xbmcvfs.delete(result.filepath)
