#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 2017年2月16日
@author: shuai.chen
'''

from __future__ import absolute_import

from abc import ABCMeta

import redis
import cPickle as pickle

from .codis import Connection
from towgo.msetting import settings

class _Cache(object):
    '''
    REDIS cache base API
    '''   
    __metaclass__ = ABCMeta

    def __getattr__(self, attr):
        return getattr(self.conn, attr)
         
    def get_conn(self):
        return self.conn
    
    def __set(self,key,value,expire=0,add_only=False):
        """
        REDIS set
        @param param: 
            key: KEY
            value: VALUE
            expire:生命期   单位s
            add_only:是否只增加不覆盖   默认覆盖
        """
        if expire > 0:
            if add_only:
                added = self.conn.setnx(key, value)
                if added:
                    self.conn.expire(key, expire)
                return added
            return self.conn.setex(key, value, expire)            
        else:
            if add_only:
                return self.conn.setnx(key, value)
            return self.conn.set(key, value)            

    def set(self, key, value, expire=0):
        """
            设置string型数据
        """
        return self.__set(key, value, expire)    

    def get(self, key):
        """
            获取string型 数据
        """
        return self.conn.get(key)
    
    def set_obj(self, key, data, expire=0):
        """
            存储 PYTHON 对象   
        """
        if data is None:
            return False
        val = pickle.dumps(data, pickle.HIGHEST_PROTOCOL)
        return self.__set(key, val, expire)
        
    def get_obj(self, key):  
        """
            获取 PYTHON 对象    
        """  
        val = self.conn.get(key)
        if val is None:
            return None
        return pickle.loads(val) 
  
class RedisCache(_Cache):
    """
    @example:
        from towgo.cache.db_cache import RedisCache      
        cache = RedisCache()
        cache.set('a',1) 
        cache.conn.sadd('x','a')    
    """
    _pools = {}

    def __new__(cls, conn_name='default', *args, **kwargs):
        if conn_name not in cls._pools:
            cls.connect(conn_name, **kwargs)
        return super(RedisCache, cls).__new__(cls)
    
    def __init__(self,conn_name='default', *args, **kwargs):
        self.conn = redis.Redis(connection_pool = self._pools[conn_name])  

    @classmethod
    def connect(cls, conn_name, **kwargs):
        config = kwargs or settings.REDIS[conn_name]
        cls._pools[conn_name] = redis.ConnectionPool(**config)
       
class CodisCache(_Cache):
    """
    @example:
        from towgo.cache.db_cache import CodisCache      
        cache = CodisCache()
        cache.set('a',1) 
        cache.conn.sadd('x','a')    
    """
    _connections = {}
    
    def __new__(cls, conn_name='default', *args, **kwargs):
        if conn_name not in cls._connections:
            cls.connect(conn_name, **kwargs)
        return super(CodisCache, cls).__new__(cls)

    def __init__(self, conn_name='default', *args, **kwargs):
        self.conn = self._connections[conn_name].getResource()
        
    @classmethod
    def connect(cls, conn_name, **kwargs):   
        configs = kwargs or settings.CODIS[conn_name]
        cls._connections[conn_name] = Connection(**configs)
