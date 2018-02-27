#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 2017年1月4日
@author: shuai.chen
'''

from __future__ import absolute_import

import logging
from .mlogger import MultiProcessTimedRotatingFileHandler

class Logger(object):
    
    _fmt = "[%(asctime)s]-%(filename)s:%(lineno)s-%(levelname)s - %(message)s"
          
    def __init__(self, ft, log_file, level, 
                       when='MIDNIGHT', backup_count=10, 
                       suffix="%Y-%m-%d", console=False,
                       fmt=""):
        """
        @param param: 
            ft : log sign
            log_file : log file
            console : Is it need to output in console?
            fmt : log formatter
        """
        self.fmt = fmt or self._fmt
        self.logger = logging.getLogger(ft)     
           
        self.initialize(log_file, when, backup_count, suffix, console)    
        self.set_level(level)   

    def initialize(self,fname, when, backup_count, suffix, console):      
        filehandle = MultiProcessTimedRotatingFileHandler(fname, when, 1,
                                                backupCount=backup_count, encoding="utf-8")
        filehandle.suffix = suffix         
        formatter = logging.Formatter(fmt=self.fmt)
        filehandle.setFormatter(formatter)
        self.logger.addHandler(filehandle)  
    
        if console:
            consolehandle = logging.StreamHandler() 
            consolehandle.setFormatter(formatter)            
            self.logger.addHandler(consolehandle)          
   
    def get_logger(self):
        return self.logger
           
    def set_level(self, level):
        logger_level = getattr(logging, level, logging.INFO)
        self.logger.setLevel(logger_level) 
        