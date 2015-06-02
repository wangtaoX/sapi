#!/usr/bin/env python
# encoding: utf-8
from neutron import context
from neutron.agent import rpc as agent_rpc

class PluginApi(agent_rpc.PluginApi):
    pass

class RpcClient():
    def __init__(self, topic):
        self.topic = topic
        self.context = context.get_admin_context_without_session()
        self.rpc = PluginApi(self.topic)

    @classmethod
    def create(cls, topic):
        rpc = cls(topic)
        return rpc

    def tunnel_sync(self, ip, type):
        return self.rpc.tunnel_sync(self.context, ip, type)
