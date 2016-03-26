import AppKit
import tempfile
import os
import shutil
import webbrowser
import subprocess
import sys


from appdirs import user_data_dir
from datetime import datetime
from StringIO import StringIO
from zipfile import ZipFile
from urllib import urlopen
from PyObjCTools import AppHelper

from twisted.internet import _threadedselect
_threadedselect.install()
from twisted.internet import reactor, defer
from twisted.web import server, static

from lbrynet.lbrynet_daemon.LBRYDaemon import LBRYDaemon, LBRYindex, LBRYDaemonWeb, LBRYFileRender
from lbrynet.conf import API_ADDRESS, API_CONNECTION_STRING, API_PORT, API_INTERFACE, DEFAULT_WALLET, ICON_PATH, APP_NAME
from lbrynet.conf import UI_ADDRESS
from LBRYNotify import LBRYNotify


class LBRYDaemonApp(AppKit.NSApplication):
    def finishLaunching(self):
        self.connection = False
        statusbar = AppKit.NSStatusBar.systemStatusBar()
        self.statusitem = statusbar.statusItemWithLength_(AppKit.NSVariableStatusItemLength)

        self.icon = AppKit.NSImage.alloc().initByReferencingFile_(ICON_PATH)
        self.icon.setScalesWhenResized_(True)
        self.icon.setSize_((20, 20))
        self.statusitem.setImage_(self.icon)

        self.menubarMenu = AppKit.NSMenu.alloc().init()

        self.open = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Open", "openui:", "")
        self.menubarMenu.addItem_(self.open)

        self.quit = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit", "terminate:", "")
        self.menubarMenu.addItem_(self.quit)

        self.statusitem.setMenu_(self.menubarMenu)
        self.statusitem.setToolTip_(APP_NAME)

        LBRYNotify("Starting LBRY")

        def getui():
            def download_ui(dest_dir):
                url = urlopen("https://rawgit.com/lbryio/lbry-web-ui/master/dist.zip")
                z = ZipFile(StringIO(url.read()))
                z.extractall(dest_dir)
                return defer.succeed(dest_dir)

            data_dir = user_data_dir("LBRY")
            version_dir = os.path.join(data_dir, "ui_version_history")

            git_version = subprocess.check_output("git ls-remote https://github.com/lbryio/lbry-web-ui.git | grep HEAD | cut -f 1", shell=True)

            if not os.path.isdir(data_dir):
                os.mkdir(data_dir)

            if not os.path.isdir(os.path.join(data_dir, "ui_version_history")):
                os.mkdir(version_dir)

            if not os.path.isfile(os.path.join(version_dir, git_version)):
                try:
                    f = open(os.path.join(version_dir, git_version), "w")
                    version_message = "Updating UI " + str(datetime.now())
                    f.write(version_message)
                    f.close()
                except:
                    LBRYNotify("You should have been notified to install xcode command line tools, once it's installed you can start LBRY")
                    sys.exit(0)

                if os.path.isdir(os.path.join(data_dir, "lbry-web-ui")):
                    os.rmdir(os.path.join(data_dir, "lbry-web-ui"))

            if os.path.isdir(os.path.join(data_dir, "lbry-web-ui")):
                return defer.succeed(os.path.join(data_dir, "lbry-web-ui"))
            else:
                return download_ui((os.path.join(data_dir, "lbry-web-ui")))

        def setupserver(ui_dir):
            root = LBRYindex(ui_dir)
            root.putChild("css", static.File(os.path.join(ui_dir, "css")))
            root.putChild("font", static.File(os.path.join(ui_dir, "font")))
            root.putChild("img", static.File(os.path.join(ui_dir, "img")))
            root.putChild("js", static.File(os.path.join(ui_dir, "js")))
            root.putChild("webapi", LBRYDaemonWeb())
            root.putChild("view", LBRYFileRender())
            return defer.succeed(root)

        def setupapi(root):
            daemon = LBRYDaemon()
            root.putChild(API_ADDRESS, daemon)
            reactor.listenTCP(API_PORT, server.Site(root), interface=API_INTERFACE)
            return daemon.setup(DEFAULT_WALLET, "False")

        d = getui()
        d.addCallback(setupserver)
        d.addCallback(setupapi)
        d.addCallback(lambda _: webbrowser.get("safari").open(UI_ADDRESS))

        reactor.interleave(AppHelper.callAfter)

    def openui_(self, sender):
        webbrowser.get('safari').open(UI_ADDRESS)

    def replyToApplicationShouldTerminate_(self, shouldTerminate):
        LBRYNotify("Goodbye!")
        reactor.stop()
