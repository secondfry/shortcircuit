# navprocessor.py
import os

from PySide2 import QtCore

from .navigation import Navigation


class NavProcessor(QtCore.QObject):
  """
  Navigation Processor (will work in a separate thread)
  """

  finished = QtCore.Signal(int, int)

  def __init__(self, nav: Navigation, parent=None):
    super().__init__(parent)
    self.evescout_enable = False
    self.nav = nav

  def process(self):
    if 'DEBUG' in os.environ:
      import debugpy
      debugpy.debug_this_thread()

    solar_map = self.nav.reset_chain()
    
    # Setup mappers based on configuration
    self.nav.setup_mappers(evescout_enable=self.evescout_enable)
    
    # Augment from all registered mappers
    results = self.nav.augment_from_all_mappers(solar_map)
    
    # Extract connection counts for backward compatibility
    tripwire_connections = results.get("Tripwire", 0)
    evescout_connections = results.get("Eve Scout", 0)
    
    # Update solar map if we got any connections
    if tripwire_connections > 0 or evescout_connections > 0:
      self.nav.solar_map = solar_map
      
    self.finished.emit(tripwire_connections, evescout_connections)
