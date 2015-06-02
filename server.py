#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import traceback
moudule_dir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
                            os.pardir,os.pardir))
sys.path.insert(0, moudule_dir)

from paste import deploy
from oslo.config import cfg
from wsgiref.simple_server import make_server

from neutron.common import config as common_config

#default configuration
OPTS_DEFAULT = [
    cfg.StrOpt("app", default="sapi",
        help="application name"),
    cfg.StrOpt("sapi_bind_host", default="127.0.0.1",
        help="The host IP to bind to"),
    cfg.IntOpt("sapi_bind_port", default=8080,
        help="The port to bind to"),
    cfg.StrOpt("version", default="0.0.0",
        help="application version"),
    cfg.StrOpt("paste_file", default="sapi-paste.ini",
        help="The API paste config file to use"),
]

#swicth driver configuretion
SWITCH_OPTS = [
    cfg.StrOpt("h3c", default="h3c"),
    cfg.StrOpt("pica8", default="pica8"),
]
GRPS = [
    cfg.OptGroup(name="switchs", title="switch drivers")
]

def register_opts(conf):
    for grps in GRPS:
        conf.register_group(grps)
    conf.register_opts(SWITCH_OPTS, group="switchs")
    conf.register_opts(OPTS_DEFAULT)

def server(app_name, ini_file, host, port):
    app = load_paste_app(app_name, ini_file)
    serve = make_server(host, port, app)
    serve.serve_forever()

def load_paste_app(app_name, ini_file):
    try:
        config_file = "config:%s" %(os.path.abspath(ini_file))
        app = deploy.loadapp(config_file, name=app_name)
        return app
    except:
        print traceback.format_exc()

if __name__ == "__main__":
    register_opts(cfg.CONF)
    common_config.init(sys.argv[1:])
    app_name = cfg.CONF['app']
    ini_file = cfg.CONF['paste_file']
    host, port = cfg.CONF['sapi_bind_host'], cfg.CONF['sapi_bind_port']
    server(app_name, ini_file, host, port)
