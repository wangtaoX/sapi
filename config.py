#!/usr/bin/env python
# encoding: utf-8

from oslo.config import cfg
from oslo import messaging

#neutron rpc setup
messaging.set_transport_defaults(control_exchange='neutron')

def init(args, **kwargs):
    #initialize neutron rpc.
    from torconf import common_rpc as n_rpc
    n_rpc.init(cfg.CONF)

    #load config from file.
    cfg.CONF(args=args, **kwargs)
