# logger.py

import logging
import sys
from logging.handlers import RotatingFileHandler
from utility.singleton import Singleton
from pprint import pprint
from PySide import QtCore


class Logger:
  __metaclass__ = Singleton

  def __init__(self):
    logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] %(message)s")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)

    fileHandler = RotatingFileHandler('shortcircuit.log', maxBytes=1024*1024, backupCount=2)
    fileHandler.setFormatter(logFormatter)
    fileHandler.setLevel(logging.DEBUG)
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    consoleHandler.setLevel(logging.INFO)
    rootLogger.addHandler(consoleHandler)

    self.threads = {}

  @staticmethod
  def register_thread(thread, name):
    Logger().threads[thread] = {
      'name': name
    }

  @staticmethod
  def get_thread_name(thread):
    if thread in Logger().threads:
      return Logger().threads[thread]['name']
    return thread

  @staticmethod
  def get_caller(origin=None, func=None):
    caller = sys._getframe().f_back # caller is prepare_message
    caller = caller.f_back # caller is our logging function
    caller = caller.f_back # caller is finally proper function
    if func:
      caller_function_name = func
    else:
      caller_function_name = caller.f_code.co_name
    if origin:
      caller_class_name = origin
    else:
      caller_class_name = caller.f_locals.get('self', None)
      if caller_class_name:
        caller_class_name = caller_class_name.__class__.__name__
    return (caller_class_name, caller_function_name)

  @staticmethod
  def prepare_message(msg, origin=None, func=None):
    caller_class_name, caller_function_name = Logger.get_caller(origin, func)
    thread_name = Logger.get_thread_name(QtCore.QThread.currentThread())
    return '[{}] [{}.{}()]  {}'.format(thread_name, caller_class_name, caller_function_name, msg)

  @staticmethod
  def critical(msg, origin=None, func=None, *args, **kwargs):
    logging.critical(Logger.prepare_message(msg, origin, func), *args, **kwargs)

  @staticmethod
  def error(msg, origin=None, func=None, *args, **kwargs):
    logging.error(Logger.prepare_message(msg, origin, func), *args, **kwargs)

  @staticmethod
  def warning(msg, origin=None, func=None, *args, **kwargs):
    logging.warning(Logger.prepare_message(msg, origin, func), *args, **kwargs)

  @staticmethod
  def info(msg, origin=None, func=None, *args, **kwargs):
    logging.info(Logger.prepare_message(msg, origin, func), *args, **kwargs)

  @staticmethod
  def debug(msg, origin=None, func=None, *args, **kwargs):
    logging.debug(Logger.prepare_message(msg, origin, func), *args, **kwargs)
