def main():
  import sys
  from shortcircuit.model.logger import Logger
  from shortcircuit import app

  Logger()
  sys.exit(app.run())


if __name__ == "__main__":
  main()
