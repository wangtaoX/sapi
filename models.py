#!/usr/bin/env python
# encoding: utf-8
import sqlalchemy as sa

from torconf import model_base
from torconf import db

class SapiProvisionedNets(model_base.BASE):
    __tablename__ = "sapi_provisioned_nets"

    network_id = sa.Column(sa.String(36), primary_key = True)
    tenant_id = sa.Column(sa.String(255))
    segmentation_id = sa.Column(sa.Integer)
    segmentation_type = sa.Column(sa.String(36))
    admin_state_up = sa.Column(sa.Boolean)
    shared = sa.Column(sa.Boolean)

    def sapi_net_representation(self):
        return {'network_id': self.network_id,
                'tenant_id': self.tenant_id,
                'segmentation_id': self.segmentation_id,
                'segmentation_type': self.segmentation_type,
                'admin_state_up': self.admin_state_up,
                'shared': self.shared}

def update_net(network_id, net):
    session = db.get_session()
    with session.begin():
        n = (session.query(SapiProvisionedNets).
                filter_by(network_id=network_id).one())
        n.update(net)

def save_net(net):
    session = db.get_session()
    with session.begin():
        net = SapiProvisionedNets(network_id=net["network_id"],
                tenant_id=net["tenant_id"],
                segmentation_id=net["segmentation_id"],
                segmentation_type=net["segmentation_type"],
                admin_state_up=net["admin_state_up"],
                shared=net["shared"])
        session.add(net)

def delete_net(network_id):
    session = db.get_session()
    with session.begin():
        (session.query(SapiProvisionedNets).
                filter_by(network_id=network_id).delete())

def get_net(network_id):
    session = db.get_session()
    with session.begin():
        net = (session.query(SapiProvisionedNets).
                filter_by(network_id=network_id).one())
        return net.sapi_net_representation()

def clear_nets():
    session = db.get_session()
    with session.begin():
        (session.query(SapiProvisionedNets).delete())

def get_nets():
    session = db.get_session()
    with session.begin():
        nets = (session.query(SapiProvisionedNets))
        return dict((net.network_id, net.sapi_net_representation()) for net in nets)

class SapiTor(model_base.BASE):
    __tablename__ = "sapi_tor"

    tor_ip = sa.Column(sa.String(45), primary_key=True)
    tunnel_src_ip = sa.Column(sa.String(45), primary_key=True)
    type = sa.Column(sa.String(45), primary_key=True)

    def sapi_tor_representation(self):
        return {"tor_ip": self.tor_ip,
                "tunnel_src_ip": self.tunnel_src_ip,
                "type": self.type}

def save_tor(tor):
    session = db.get_session()
    with session.begin():
        tor = SapiTor(tor_ip=tor["tor_ip"],
                tunnel_src_ip=tor["tunnel_src_ip"],
                type=tor["type"])
        session.add(tor)

def delete_tor(tor_ip):
    session = db.get_session()
    with session.begin():
        (session.query(SapiTor).
                filter_by(tor_ip=tor_ip).delete())

def get_tor(tor_ip):
    session = db.get_session()
    with session.begin():
        tor = (session.query(SapiTor).
                filter_by(tor_ip=tor_ip).one())
        return tor.sapi_tor_representation()

def get_tors():
    session = db.get_session()
    with session.begin():
        tors = (session.query(SapiTor))
        return dict((tor.tor_ip, tor.sapi_tor_representation()) for tor in tors)

class SapiProvisionedPorts(model_base.BASE):
    __tablename__ = "sapi_provisioned_ports"

    port_id = sa.Column(sa.String(36), primary_key = True)
    network_id = sa.Column(sa.String(36))
    tenant_id = sa.Column(sa.String(255))
    subnet_id = sa.Column(sa.String(36))
    device_id = sa.Column(sa.String(255))
    device_owner = sa.Column(sa.String(40))
    status = sa.Column(sa.String(40))
    admin_state_up = sa.Column(sa.Boolean)
    binding_host_id = sa.Column(sa.String(40))
    mac_address = sa.Column(sa.String(255))
    ip_address = sa.Column(sa.String(255))

    def sapi_port_representation(self):
        return {'port_id': self.port_id,
                'tenant_id': self.tenant_id,
                'network_id': self.network_id,
                'subnet_id': self.subnet_id,
                'device_id': self.device_id,
                'device_owner': self.device_owner,
                'status': self.status,
                'admin_state_up': self.admin_state_up,
                'binding_host_id': self.binding_host_id,
                'ip_address': self.ip_address,
                'mac_address': self.mac_address}

def update_port(port_id, port):
    session = db.get_session()
    with session.begin():
        p = (session.query(SapiProvisionedPorts).
                filter_by(port_id=port_id).one())
        p.update(port)

def save_port(port):
    session = db.get_session()
    with session.begin():
        port = SapiProvisionedPorts(
                port_id = port['port_id'],
                tenant_id = port['tenant_id'],
                network_id = port['network_id'],
                subnet_id = port['subnet_id'],
                device_id = port['device_id'],
                device_owner = port['device_owner'],
                status = port['status'],
                admin_state_up = port['admin_state_up'],
                binding_host_id = port['binding_host_id'],
                ip_address = port['ip_address'],
                mac_address = port['mac_address'])
        session.add(port)

def delete_port(port_id):
    session = db.get_session()
    with session.begin():
        (session.query(SapiProvisionedPorts).
                filter_by(port_id=port_id).delete())

def get_port(port_id):
    session = db.get_session()
    with session.begin():
        port = (session.query(SapiProvisionedPorts).
                filter_by(port_id=port_id).one())
        return port.sapi_port_representation()

def clear_ports():
    session = db.get_session()
    with session.begin():
        (session.query(SapiProvisionedPorts).delete())

def get_ports():
    session = db.get_session()
    with session.begin():
        ports = (session.query(SapiProvisionedPorts))
        return dict((port.network_id, port.sapi_port_representation()) for port in ports)

class SapiProvisionedSubnets(model_base.BASE):
    __tablename__ = "sapi_provisioned_subnets"

    subnet_id = sa.Column(sa.String(36), primary_key=True)
    tenant_id = sa.Column(sa.String(36))
    network_id = sa.Column(sa.String(36))
    shared = sa.Column(sa.Boolean)
    enable_dhcp = sa.Column(sa.Boolean)

    def sapi_subnet_representation(self):
        return {'subnet_id': self.subnet_id,
                'network_id': self.network_id,
                'tenant_id': self.tenant_id,
                'shared': self.shared,
                'enable_dhcp': self.enable_dhcp}

def save_subnet(subnet):
    session = db.get_session()
    with session.begin():
        subnet = SapiProvisionedSubnets(
                tenant_id = subnet['tenant_id'],
                network_id = subnet['network_id'],
                subnet_id = subnet['subnet_id'],
                enable_dhcp = subnet['enable_dhcp'],
                shared = subnet['shared'])
        session.add(subnet)

def update_subnet(subnet_id, subnet):
    session = db.get_session()
    with session.begin():
        s = (session.query(SapiProvisionedSubnets).
                filter_by(subnet_id=subnet_id).one())
        s.update(subnet)

def delete_subnet(subnet_id):
    session = db.get_session()
    with session.begin():
        (session.query(SapiProvisionedSubnets).
                filter_by(subnet_id=subnet_id).delete())

def get_subnet(subnet_id):
    session = db.get_session()
    with session.begin():
        subnet = (session.query(SapiProvisionedSubnets).
                filter_by(subnet_id=subnet_id).one())
        return subnet.sapi_subnet_representation()

def clear_subnets():
    session = db.get_session()
    with session.begin():
        (session.query(SapiProvisionedSubnets).delete())

def get_subnets():
    session = db.get_session()
    with session.begin():
        subnets = (session.query(SapiProvisionedSubnets))
        return dict((subnet.subnet_id, subnet.sapi_subnet_representation()) for subnet in subnets)
