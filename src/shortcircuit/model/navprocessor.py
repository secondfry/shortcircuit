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
    self.nav = nav

  def process(self):
    if 'DEBUG' in os.environ:
      import debugpy
      debugpy.debug_this_thread()

    solar_map = self.nav.reset_chain()
    
    # Setup mappers based on configuration
    self.nav.setup_mappers()
    
    # Augment from all registered mappers
    results = self.nav.augment_map(solar_map)
    
    # Calculate total connections from all sources
    total_connections = sum(count for count in results.values() if count > 0)
    
    # For backward compatibility with UI, extract specific mapper counts
    # TODO: rethink status bar to support dynamic list of mappers
    # The UI currently expects (tripwire_connections, evescout_connections)
    tripwire_connections = results.get("Tripwire", 0)
    evescout_connections = results.get("Eve Scout", 0)
    
    # Update solar map if we got any connections
    if total_connections > 0:
      self.nav.solar_map = solar_map
      
    self.finished.emit(tripwire_connections, evescout_connections)
