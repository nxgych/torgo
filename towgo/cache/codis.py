#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 2017年2月16日
@author: shuai.chen
'''

import json
import threading
import redis
from kazoo.client import KazooClient

lock = threading.Lock()
BOOLEAN = "False"

class Connection(object):
    '''
    codis connection 
    '''
    
    def __init__(self, *args, **kwargs): 
        '''
        @param param: 
               zookeeper_address: zookeeper address
               zookeeper_path: codis proxy path
               
               pool: use redis pool if True, default is False
        '''       
        self.__zkAddr = kwargs.pop('zookeeper_address', '127.0.0.1:2181')
        self.__proxyPath = kwargs.pop('zookeeper_path', '/jodis/cache')
        
        self.__pool = kwargs.pop('pool', False)
        self.__businessID = kwargs.pop('business_id', '')
        
        self.__kwargs = kwargs
        
        self.__zk = KazooClient(self.__zkAddr)
        self.__connPoolIndex = -1
        self.__connPool = []
        self.__InitFromZK()

    def __InitFromZK(self):
        global BOOLEAN
        BOOLEAN="True"
        lock.acquire()
        try:
            self.__proxylist = []
            self.__connPool = []
            self.__zk.start()
            proxynamelist = self.__zk.get_children(self.__proxyPath,watch=self.__watcher)
            for proxy in proxynamelist:
                self.__zk.start()
                proxyinfo = self.__zk.get(self.__proxyPath+'/'+proxy,watch=self.__watcher)
                decoded = json.loads(proxyinfo[0].decode('UTF8'))
                if decoded["state"] == "online":
                    self.__proxylist.append(decoded)
            
            if self.__pool:        
                for proxyinfo in self.__proxylist:
                    proxyip = proxyinfo["addr"].split(':')[0]
                    proxyport = proxyinfo["addr"].split(':')[1]
                    conn = redis.Redis(
                        connection_pool=redis.ConnectionPool(
                            host=proxyip, port=int(proxyport), decode_responses=True, **self.__kwargs),
                    )
                    self.__connPool.append(conn)
            else:
                for proxyinfo in self.__proxylist:
                    proxyip = proxyinfo["addr"].split(':')[0]
                    proxyport = proxyinfo["addr"].split(':')[1]
                    conn = redis.Redis(host=proxyip, port=int(proxyport), decode_responses=True, **self.__kwargs)
                    self.__connPool.append(conn)          
        except:
            raise
        finally:
            BOOLEAN="False"
            lock.release()
        
    def __getProxy(self):
        lock.acquire()
        self.__connPoolIndex += 1
        if self.__connPoolIndex >= len(self.__connPool):
            self.__connPoolIndex = 0
        if len(self.__connPool) == 0:
            lock.release()
            return None
        else:
            conn = self.__connPool[self.__connPoolIndex]
            lock.release()
            return conn

    def __watcher(self, event):
        if event.type == "SESSION" and event.state == "CONNECTING":
            pass
        elif event.type == "SESSION" and event.state == "EXPIRED_SESSION":  
            self.__zk.stop()
            self.__zk = KazooClient(self.__zkAddr)
        elif event.type == "CREATED" and event.state == "CONNECTED":  
            self.__InitFromZK()
        elif event.type == "DELETED" and event.state == "CONNECTED":  
            self.__InitFromZK()
        elif  event.type == "CHANGED" and event.state == "CONNECTED":  
            self.__InitFromZK()
        elif  event.type == "CHILD" and event.state == "CONNECTED":  
            self.__InitFromZK()
        else:
            raise
        
    def convertKey(self, key):
        return '{0}_{1}'.format(self.__businessID, key) if self.__businessID else key

    def getResource(self):
        return self.__getProxy()

    def close(self):
        try:
            self.__zk.stop()
            self.__connPool = []
        except Exception:
            raise
        