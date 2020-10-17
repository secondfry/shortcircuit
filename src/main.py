import sys

from shortcircuit import app
from shortcircuit.model.logger import Logger


def main():
  Logger()
  sys.exit(app.run())


if __name__ == "__main__":
  main()
