import AppKit
import tempfile
import os
import shutil
import webbrowser

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

        self.quit = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit", "terminate:", "")
        self.menubarMenu.addItem_(self.quit)

        self.statusitem.setMenu_(self.menubarMenu)
        self.statusitem.setToolTip_(APP_NAME)

        LBRYNotify("Starting LBRY")

        def getui():
            d = defer.Deferred(None)
            self.tmpdir = tempfile.mkdtemp()

            d.addCallback(lambda _: urlopen("https://rawgit.com/lbryio/lbry-web-ui/master/dist.zip"))
            d.addCallback(lambda url: ZipFile(StringIO(url.read())))
            d.addCallback(lambda z: z.extractall(self.tmpdir))

            return d

        def setupserver(daemon):
            root = LBRYindex(self.tmpdir)
            root.putChild("css", static.File(os.path.join(self.tmpdir, "css")))
            root.putChild("font", static.File(os.path.join(self.tmpdir, "font")))
            root.putChild("img", static.File(os.path.join(self.tmpdir, "img")))
            root.putChild("js", static.File(os.path.join(self.tmpdir, "js")))
            root.putChild(API_ADDRESS, daemon)
            root.putChild("webapi", LBRYDaemonWeb())
            root.putChild("view", LBRYFileRender())
            reactor.listenTCP(API_PORT, server.Site(root), interface=API_INTERFACE)

            return defer.succeed(True)


        daemon = LBRYDaemon()
        d = getui()
        d.addCallback(lambda _: setupserver(daemon))
        d.addCallback(lambda _: daemon.setup(DEFAULT_WALLET, "False"))
        d.addCallback(lambda _: webbrowser.get('safari').open("http://localhost:5279"))
        d.callback(None)

        reactor.interleave(AppHelper.callAfter)

    def replyToApplicationShouldTerminate_(self, shouldTerminate):
        LBRYNotify("Goodbye!")
        shutil.rmtree(self.tmpdir)
        reactor.stop()
