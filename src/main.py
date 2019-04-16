__version__ = '0.4.0'
__date__ = '2019-04-16'
__appname__ = 'Short Circuit'

def main():
  import sys
  from shortcircuit.model.logger import Logger
  from shortcircuit import app

  Logger()
  sys.exit(app.run())


if __name__ == "__main__":
  main()
