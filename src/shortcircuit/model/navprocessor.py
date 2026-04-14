# navprocessor.py
import os

from PySide2 import QtCore

from .navigation import Navigation


class NavProcessor(QtCore.QObject):
  """
  Navigation Processor (will work in a separate thread)
  """

  finished = QtCore.Signal(dict)

  def __init__(self, nav: Navigation, parent=None):
    super().__init__(parent)
    self.nav = nav

  def process(self):
    if 'DEBUG' in os.environ:
      import debugpy
      debugpy.debug_this_thread()

    solar_map = self.nav.reset_chain()
    self.nav.setup_mappers()
    results = self.nav.augment_map(solar_map)

    total_connections = sum(count for count in results.values() if count > 0)
    if total_connections > 0:
      self.nav.solar_map = solar_map

    self.finished.emit(results)
