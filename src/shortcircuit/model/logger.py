# logger.py

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from appdirs import AppDirs
from PySide6 import QtCore

from shortcircuit import __appslug__, __version__
from .utility.singleton import Singleton


class Logger(metaclass=Singleton):

  def __init__(self):
    log_formatter = logging.Formatter(
      "%(asctime)s [%(levelname)-5.5s] %(message)s"
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    app_dirs = AppDirs(__appslug__, "secondfry", version=__version__)
    if not os.path.isdir(app_dirs.user_log_dir):
      os.makedirs(app_dirs.user_log_dir)
    log_file = os.path.join(app_dirs.user_log_dir, 'shortcircuit.log')
    file_handler = RotatingFileHandler(
      log_file, maxBytes=1024 * 1024, backupCount=7
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    self.threads = {}

  @staticmethod
  def register_thread(thread: QtCore.QThread, name: str):
    Logger().threads[thread] = {'name': name}

  @staticmethod
  def get_thread_name(thread: QtCore.QThread):
    if thread in Logger().threads:
      return Logger().threads[thread]['name']
    return thread

  @staticmethod
  def get_caller(origin: str = None, func: str = None):
    caller = sys._getframe().f_back  # caller is prepare_message
    caller = caller.f_back  # caller is our logging function
    caller = caller.f_back  # caller is finally proper function
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
    return caller_class_name, caller_function_name

  @staticmethod
  def prepare_message(msg, origin: str = None, func: str = None):
    caller_class_name, caller_function_name = Logger.get_caller(origin, func)
    thread_name = Logger.get_thread_name(QtCore.QThread.currentThread())
    return '[{}] [{}.{}()]  {}'.format(
      thread_name, caller_class_name, caller_function_name, msg
    )

  @staticmethod
  def critical(msg, origin: str = None, func: str = None, *args, **kwargs):
    logging.critical(Logger.prepare_message(msg, origin, func), *args, **kwargs)

  @staticmethod
  def error(msg, origin: str = None, func: str = None, *args, **kwargs):
    logging.error(Logger.prepare_message(msg, origin, func), *args, **kwargs)

  @staticmethod
  def warning(msg, origin: str = None, func: str = None, *args, **kwargs):
    logging.warning(Logger.prepare_message(msg, origin, func), *args, **kwargs)

  @staticmethod
  def info(msg, origin: str = None, func: str = None, *args, **kwargs):
    logging.info(Logger.prepare_message(msg, origin, func), *args, **kwargs)

  @staticmethod
  def debug(msg, origin: str = None, func: str = None, *args, **kwargs):
    logging.debug(Logger.prepare_message(msg, origin, func), *args, **kwargs)
