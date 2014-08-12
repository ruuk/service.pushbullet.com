# -*- coding: utf-8 -*-
import xbmcaddon

ADDON = xbmcaddon.Addon()

def LOG(msg):
	print 'service.pushbullet.com: {0}'.format(msg)
	
def getSetting(key):
	return ADDON.getSetting(key)

def setSetting(key,value):
	return ADDON.setSetting(key, value)