from PyObjCTools import AppHelper
import logging
from LBRYApp import LBRYDaemonApp

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def main():
    app = LBRYDaemonApp.sharedApplication()
    AppHelper.runEventLoop()

if __name__ == "__main__":
    main()
