# -*- coding: utf-8 -*-
import xbmc, xbmcaddon

ADDON = xbmcaddon.Addon()

def LOG(msg):
	 xbmc.log('service.pushbullet.com: {0}'.format(msg))
	
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