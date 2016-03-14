import logging
import os
import json
import webbrowser
import sys
import AppKit
from PyObjCTools import AppHelper

from twisted.internet import _threadedselect
_threadedselect.install()
from twisted.internet import reactor
from twisted.web import server

from lbrynet.lbrynet_daemon.LBRYDaemon import LBRYDaemon, LBRYindex, LBRYDaemonWeb, LBRYFilePage
from lbrynet.conf import API_ADDRESS, API_CONNECTION_STRING, API_PORT, API_INTERFACE, DEFAULT_WALLET, ICON_PATH, APP_NAME
from jsonrpc.proxy import JSONRPCProxy

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class LBRYApp(AppKit.NSApplication):
    def finishLaunching(self):
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

        daemon = LBRYDaemon()
        reactor.callLater(0.0, daemon.setup, DEFAULT_WALLET, "False")

        root = LBRYindex()
        root.putChild("", root)
        root.putChild("webapi", LBRYDaemonWeb())
        root.putChild(API_ADDRESS, daemon)
        root.putChild("mylbry", LBRYFilePage())

        reactor.listenTCP(API_PORT, server.Site(root), interface="localhost")
        reactor.interleave(AppHelper.callAfter)

        # webbrowser.get('safari').open("http://%s:%i" % (API_INTERFACE, API_PORT))

    # def applicationShouldTerminate_(self, sender):
    #     log.info("Trying to stop reactor")
    #     reactor.stop()

    def replyToApplicationShouldTerminate_(self, shouldTerminate):
        reactor.stop()


def urihandler(args):
    log.info("start url handler")

    if len(args) == 0:
        args.append("lbry://wonderfullife")

    daemon = JSONRPCProxy.from_url(API_CONNECTION_STRING)

    try:
        s = daemon.is_running()
        log.info(s)
        log.info(args)

        if len(args) > 1:
            exit(1)

        if args[0][7:] == "lbry":
            webbrowser.get('safari').open("http://%s:%i" % (API_INTERFACE, API_PORT))

        # elif args[0][7:] == "settings":
        #     r = daemon.get_settings()
        #     html = "<body>" + str(r) + "</body>"
        #     daemon.render_html(html)

        # else:
        #     r = json.loads(daemon.get(args[0][7:]))['result']
        #     log.info(r)
        #     if r[0] == 200:
        #         path = r[1]['path']
        #         if path[0] != '/':
        #             path = '/' + path
        #
        #         filename = os.path.basename(path)
        #         extension = os.path.splitext(filename)[1]
        #
        #         if extension in ['mp4', 'flv', 'mov']:
        #             html = render_video(path)
        #             daemon.render_html(html)
        #         else:
        #             webbrowser.get('safari').open('file://' + str(path))
        #
        #     else:
        #         webbrowser.get('safari').open('http://lbry.io/get')

    except:
        log.info("daemon wasn't running, starting it")
        main()


def main():
    app = LBRYApp.sharedApplication()
    AppHelper.runEventLoop()

if __name__ == "__main__":
   urihandler(sys.argv[1:])
