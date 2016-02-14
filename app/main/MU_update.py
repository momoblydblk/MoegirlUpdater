# -*- coding: utf-8 -*-
import sys
reload(sys)
import datetime
import json
import urllib,urllib2
import calendar
import time
import os
from bs4 import BeautifulSoup
import logging,logging.handlers
import traceback
import weibo
import pdb
from collections import OrderedDict
sys.setdefaultencoding('utf-8')
from MU_conf import MU_MainConfig
from MU_weibo import post,PrepareLogin
from MU_utils import r,unique_str,loggingInit,for_cat,for_rc,_decode_dict
os.chdir(os.path.dirname(__file__))
log=loggingInit('../log/update.log')
def GetCategory(title):
    apiurl="http://zh.moegirl.org/api.php"
    parmas = urllib.urlencode({'format':'json','action':'query','prop':'categories','titles':title})
    req=urllib2.Request(url=apiurl,data=parmas)
    res_data=urllib2.urlopen(req)
    ori=res_data.read()
    categories=json.loads(ori, object_hook=_decode_dict)
    cat=for_cat(categories)
    return cat
def GetImage(title):
    try:
        url="http://zh.moegirl.org/"+title
        f=urllib.urlopen(url)
    except:
        return None
    src=f.read()
    f.close
    ssrc=BeautifulSoup(src,"html.parser")
    try:
        image_div=ssrc.find_all('a',class_='image')
        for i in range(len(image_div)):
            imgtag=image_div[i].find('img')
            if (int(imgtag['width']) > 200 and int(imgtag['height']) > 100): #出问题都是anna的锅
                img = imgtag['src']
                break
            else:
                continue
    except:
        return None
    isExists=os.path.exists('../imgcache')
    if not isExists:
        os.makedirs('../imgcache')
    name=unique_str()
    TheImageIsReadyToPush=False
    if locals().has_key("img"):
        try:
            with open('../imgcache/'+name,'wb') as f:
                con=urllib.urlopen("http:"+img)
                f.write(con.read())
                f.flush()
                TheImageIsReadyToPush=True
                r.hset('img',MU_MainConfig.EDITEDPREFIX+title,name)
        except BaseException, e:
                log.debug(e)
                return None
    else:
        return None
    return TheImageIsReadyToPush
def ForbiddenItemsFilter(item):
    cat=GetCategory(item)
    ForCat="Category:屏蔽更新姬推送的条目"
    for i in range(len(cat)):
        if cat[i]==ForCat.encode('utf-8'):
            return False
            break
    return True
    
def ForbiddenItemPushed(title):
    keys = r.hkeys('queue')
    if MU_MainConfig.PUSHEDPREFIX+title in keys:
        return False
    return True
def ForbiddenItemGet(title):
    keys = r.hkeys('queue')
    if MU_MainConfig.EDITEDPREFIX+title in keys:
        return False
    return True
def DeletePage(title):
    r.zrem('expire',MU_MainConfig.EDITEDPREFIX+title)
    r.hdel('queue',MU_MainConfig.EDITEDPREFIX+title)
    name=r.hget('img',MU_MainConfig.EDITEDPREFIX+title)
    os.remove('../imgcache/'+name)
    r.hdel('img',MU_MainConfig.EDITEDPREFIX+title)
    r.hdel('imgkey',title)
    score=r.zscore('queuenumber',title)
    r.zrem('queuenumber',title)
    scorequeue=r.zrange('queuenumber',int(score)-1,-1)
    for i in range(len(scorequeue)):
        score=r.zscore('queuenumber',scorequeue[i])
        r.zadd('queuenumber',scorequeue[i],score-1)
    return True
class MU_UpdateData(object):
    def __init__(self):
        super(MU_UpdateData,self).__init__()
        self.cache=[]
        self.SendFlag=False
    def initupdater(self):
        self.GetRecentChanges(2)
    def GetRecentChanges(self):
        value=for_rc()
        for i in range(len(value)):
            if value[i]['newlen']>1000:
                self.cache.append(value[i]['title'])
            else:
                pass
        return self.cache
    def FilterValid(self):
        self.GetRecentChanges()
        self.cache=filter(ForbiddenItemsFilter,self.cache)
        self.cache=filter(ForbiddenItemPushed,self.cache)
        self.cache=filter(ForbiddenItemGet,self.cache)
        return self.cache
    def SaveRecentChanges(self):
        self.FilterValid()
        for i in range(len(self.cache)):
            flag=GetImage(self.cache[i])
            if flag==True:
                itemkey=MU_MainConfig.EDITEDPREFIX+self.cache[i]
                r.hset('queue',itemkey,self.cache[i])
                timenow=time.time()
                r.zadd('expire',itemkey,timenow)
            else:
                pass
    def RemoveExpiredItems(self):
        timenow=time.time()
        ThreeDaysAgo=time.time()-MU_MainConfig.THREEDAYS
        zset=r.zrangebyscore('expire',ThreeDaysAgo,timenow)
        hkeys=r.hkeys('oriqueue')
        setofzset=set(zset)
        setofhkeys=set(hkeys)
        intersection=list(setofzset&setofhkeys)
        for i in range(len(hkeys)):
            if hkeys[i] not in intersection:
                title=hget('queue',hkeys[i])
                DeletePage(title)


    def GetItemToSend(self):
        scorequeue=r.zrevrange('queuenumber',0,-1)
        try:
            lastnumber=r.zscore('queuenumber',scorequeue[0])
            for i in range(len(self.cache)):
                scorequeue=r.zrevrange('queuenumber',0,-1)
                lastnumber=r.zscore('queuenumber',scorequeue[0])
                ToBeSendTitle=r.hget('queue',MU_MainConfig.EDITEDPREFIX+self.cache[i])
                ToBeSendImage=r.hget('img',MU_MainConfig.EDITEDPREFIX+self.cache[i])
                if ToBeSendTitle not in scorequeue:
                    r.zadd('queuenumber',ToBeSendTitle,lastnumber)
                    r.zincrby('queuenumber',ToBeSendTitle,1)
                r.hset('imgkey',ToBeSendTitle,ToBeSendImage)
        except:
            for i in range(len(self.cache)):
                ToBeSendTitle=r.hget('queue',MU_MainConfig.EDITEDPREFIX+self.cache[i])
                ToBeSendImage=r.hget('img',MU_MainConfig.EDITEDPREFIX+self.cache[i])
                r.zadd('queuenumber',ToBeSendTitle,i)
                r.zincrby('queuenumber',ToBeSendTitle,1)
                r.hset('imgkey',ToBeSendTitle,ToBeSendImage)        
    def PostItem(self):
        Keys=r.zrange('queuenumber',0,-1)
        ReadyToPostItem=Keys[0]
        UnPushed=ForbiddenItemPushed(ReadyToPostItem)
        if UnPushed is not False:
            DeletePage(ReadyToPostItem)
            r.hset('queue',MU_MainConfig.PUSHEDPREFIX+ReadyToPostItem,ReadyToPostItem)
        else:
            pass
item='123'
update=MU_UpdateData()
#update.SaveRecentChanges()
#update.RemoveExpiredItems()
#PrepareLogin()
#update.GetItemToSend()
#update.PostItem()