#!/usr/bin/env python
# encoding: utf-8
import sqlalchemy as sa

from torconf import model_base
from torconf import db

class SapiVlanAllocations(model_base.BASE):
    __tablename__ = "sapi_vlan_allocations"

    id = sa.Column(sa.Integer, primary_key=True)
    network_id = sa.Column(sa.String(255))
    tor_ip = sa.Column(sa.String(45))
    vlan_id = sa.Column(sa.Integer)
    allocated = sa.Column(sa.Boolean)
    shared = sa.Column(sa.Boolean)

    def sapi_vlan_allocations_rep(self):
        return {"network_id":self.network_id,
                "tor_ip":self.tor_ip,
                "vlan_id":self.vlan_id,
                "allocated": self.allocated,
                "shared":self.shared}

def save_vlan_allocations(va):
    session = db.get_session()
    with session.begin():
        _va = SapiVlanAllocations(network_id=va["network_id"],
                tor_ip=va["tor_ip"],
                vlan_id=va["vlan_id"],
                allocated=va["allocated"],
                shared=va["shared"])
        session.add(_va)

def delete_vlan_allocations(tor_ip, network_id):
    session = db.get_session()
    with session.begin():
        (session.query(SapiVlanAllocations).
                filter_by(tor_ip=tor_ip, network_id=network_id).delete())

def get_vlan_allocations():
    session = db.get_session()
    with session.begin():
        vas = (session.query(SapiVlanAllocations))
        return [va.sapi_vlan_allocations_rep() for va in vas]

class SapiTorTunnel(model_base.BASE):
    __tablename__ = "sapi_tor_tunnels"

    id = sa.Column(sa.Integer, primary_key=True)
    tor_ip = sa.Column(sa.String(45))
    dst_addr = sa.Column(sa.String(45))
    tunnel_id = sa.Column(sa.Integer)

    def sapi_tor_tunnels_rep(self):
        return {"tor_ip":self.tor_ip,
                "dst_addr":self.dst_addr,
                "tunnel_id":self.tunnel_id}

def save_tunnel(tt):
    session = db.get_session()
    with session.begin():
        _tt = SapiTorTunnel(tor_ip=tt["tor_ip"],
                tunnel_id=tt["tunnel_id"],
                dst_addr=tt["dst_addr"])
        session.add(_tt)

def delete_tunnel(tor_ip, id):
    session = db.get_session()
    with session.begin():
        (session.query(SapiTorTunnel).
                filter_by(tor_ip=tor_ip, tunnel_id=id).delete())

def get_tunnel_with_tor(tor_ip, dst_addr):
    session = db.get_session()
    with session.begin():
        _tts = (session.query(SapiTorTunnel).
                filter_by(tor_ip=tor_ip))
        _tts1 = (session.query(SapiTorTunnel).
                filter_by(dst_addr=dst_addr))
        return [tt.sapi_tor_tunnels_rep() for tt in _tts],\
                [tt1.sapi_tor_tunnels_rep() for tt1 in _tts1]

def get_tunnnels():
    session = db.get_session()
    with session.begin():
        tts = (session.query(SapiTorTunnel))
        return [tt.sapi_tor_tunnels_rep() for tt in tts]

class SapiPortVlanMapping(model_base.BASE):
    __tablename__ = "sapi_port_vlan_mapping"

    port_id = sa.Column(sa.String(36), primary_key = True)
    network_id = sa.Column(sa.String(36))
    tor_ip = sa.Column(sa.String(45))
    vlan_id = sa.Column(sa.INTEGER)
    index = sa.Column(sa.INTEGER)

    def sapi_port_vlan_representation(self):
        return {'port_id': self.port_id,
                'network_id': self.network_id,
                'tor_ip': self.tor_ip,
                'vlan_id': self.vlan_id,
                'index':self.index}

def save_port_vlan_mapping(pvm):
    session = db.get_session()
    with session.begin():
        _pvm = SapiPortVlanMapping(port_id=pvm["port_id"],
                network_id=pvm["network_id"],
                tor_ip=pvm["tor_ip"],
                vlan_id=pvm["vlan_id"],
                index=pvm["index"])
        session.add(_pvm)

def delete_port_vlan_mapping(port_id):
    session = db.get_session()
    with session.begin():
        (session.query(SapiPortVlanMapping).
                filter_by(port_id=port_id).delete())

def get_port_vlan_mapping(port_id):
    session = db.get_session()
    with session.begin():
        pvm = (session.query(SapiPortVlanMapping).
                filter_by(port_id=port_id).one())
        return pvm.sapi_port_vlan_representation()

def get_pvm_count_by_net(tor_ip, network_id):
    session = db.get_session()
    with session.begin():
        return (session.query(SapiPortVlanMapping).
                filter_by(tor_ip=tor_ip, network_id=network_id).count())

def get_pvm_count_by_tor_index(tor_ip, index):
    session = db.get_session()
    with session.begin():
        return (session.query(SapiPortVlanMapping).
                filter_by(tor_ip=tor_ip, index=index).count())

def is_exists_port_vlan_mapping(tor_ip, vlan_id, index):
    session = db.get_session()
    with session.begin():
        num = (session.query(SapiPortVlanMapping).
                filter_by(tor_ip=tor_ip, vlan_id=vlan_id, index=index).count())
        return num > 0

class SapiTorVsis(model_base.BASE):
    __tablename__ = "sapi_tor_vsis"

    id = sa.Column(sa.Integer, primary_key = True)
    tor_ip = sa.Column(sa.String(45))
    vxlan = sa.Column(sa.Integer)

    def sapi_vsi_rep(self):
        return {"tor_ip":self.tor_ip,
                "vxlan":self.vxlan}

def save_vsi(vsi):
    session = db.get_session()
    with session.begin():
        _vsi = SapiTorVsis(tor_ip=vsi["tor_ip"],
                vxlan=vsi["vxlan"])
        session.add(_vsi)

def delete_vsi(tor_ip, vxlan):
    session = db.get_session()
    with session.begin():
        (session.query(SapiTorVsis).
                filter_by(tor_ip=tor_ip, vxlan=vxlan).delete())

def get_vsis_by_tor(tor_ip):
    session = db.get_session()
    with session.begin():
        _vsis = (session.query(SapiTorVsis).
                filter_by(tor_ip=tor_ip))
        return [v.sapi_vsi_rep() for v in _vsis]
