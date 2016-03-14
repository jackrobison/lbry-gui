import os
from setuptools import setup
from lbrynet.conf import PROTOCOL_PREFIX, APP_NAME, ICON_PATH

APP = [os.path.join('lbrygui', 'app.py')]
# DATA_FILES = [(d, [os.path.join(d,f) for f in files]) for d, folders, files in os.walk('/Users/johnrobison/lbry-gui/lbrygui/static')]
DATA_FILES = []
DATA_FILES.append('app.icns')

OPTIONS = {
    'argv_emulation': True,
    'iconfile': ICON_PATH,
    'plist': {
        'LSUIElement': True,
        'CFBundleURLTypes': [
            {
                'CFBundleURLTypes': APP_NAME,
                'CFBundleURLSchemes': [PROTOCOL_PREFIX]
            }],
    },
    'packages': ['lbrynet', 'lbryum', 'requests', 'unqlite', ],
                 # 'six', 'os', 'twisted', 'miniupnpc', 'seccure',
                 # 'bitcoinrpc', 'txjsonrpc', 'Crypto', 'gmpy', 'yapsy', 'google.protobuf']
}


setup(
    name=APP_NAME,
    app=APP,
    options={'py2app': OPTIONS},
    data_files=DATA_FILES,
)