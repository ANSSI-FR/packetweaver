# coding: utf8
import subprocess
import os

try:
    import iptc
    HAS_IPTC = True
except ImportError:
    HAS_IPTC = False
    if os.access('/sbin/iptables', os.X_OK):
        HAS_IPTABLES = True
    else:
        HAS_IPTABLES = False


def _build_drop_frames_rule(iface, oface, mac_src, mac_dst):
    r = []
    if not isinstance(iface, type(None)):
        r.append('-i')
        r.append(str(iface))
    if not isinstance(oface, type(None)):
        r.append('-o')
        r.append(str(oface))
    if not isinstance(mac_src, type(None)):
        r.append('-s')
        r.append(mac_src)
    if not isinstance(mac_dst, type(None)):
        r.append('-d')
        r.append(mac_dst)
    r.append('-j')
    r.append('DROP')
    return r


def drop_frames(iface, oface, mac_src, mac_dst):
    r = _build_drop_frames_rule(iface, oface, mac_src, mac_dst)
    if not isinstance(oface, type(None)):
        chain_name = 'FORWARD'
    else:
        chain_name = 'INPUT'
    cmd = ['/sbin/ebtables', '-A', chain_name] + r
    subprocess.call(cmd)


def undrop_frames(iface, oface, mac_src, mac_dst):
    r = _build_drop_frames_rule(iface, oface, mac_src, mac_dst)
    if not isinstance(oface, type(None)):
        chain_name = 'FORWARD'
    else:
        chain_name = 'INPUT'
    cmd = ['/sbin/ebtables', '-D', chain_name] + r
    subprocess.call(cmd)


def _iptc_build_drop_packets_rule(iface, oface, ip_src, ip_dst, proto, port_src, port_dst, bridge=False):
    r = iptc.Rule()

    if bridge:
        m = r.create_match('physdev')
        if iface is not None:
            m.physdev_in = iface
        if oface is not None:
            m.physdev_out = oface
    else:
        if iface is not None:
            r.set_in_interface(iface)
        if oface is not None:
            r.set_out_interface(oface)
    if ip_src is not None:
        r.set_src(ip_src)
    if ip_dst is not None:
        r.set_dst(ip_dst)
    if proto is not None:
        r.set_protocol(proto)
        if port_src is not None or port_dst is None:
            if proto == 'tcp':
                m = r.create_match('tcp')
            else:
                m = r.create_match('udp')
            if port_src is not None:
                m.source_port = str(port_src)
            if port_dst is not None:
                m.destination_port = str(port_dst)
    r.create_target('DROP')
    return r


def _iptc_drop_packets(iface, oface, ip_src, ip_dst, proto, port_src, port_dst, bridge=False):
    if oface is not None:
        chain_name = 'FORWARD'
    else:
        chain_name = 'INPUT'

    r = _iptc_build_drop_packets_rule(iface, oface, ip_src, ip_dst, proto, port_src, port_dst, bridge)
    c = iptc.Chain(iptc.Table(iptc.Table.FILTER), chain_name)
    c.append_rule(r)


def _cmd_build_drop_packets_rule(iface, oface, ip_src, ip_dst, proto, port_src, port_dst, bridge = False):
    rule = []

    if bridge:
        rule += ['-m', 'physdev']
        if iface is not None:
            rule += ['--physdev-in', iface]
        if oface is not None:
            rule += ['--physdev-out', oface]
    else:
        if iface is not None:
            rule += ['-i', iface]
        if oface is not None:
            rule += ['-o', oface]

    if ip_src is not None:
        rule += ['--src', ip_src]
    if ip_dst is not None:
        rule += ['--dst', ip_dst]

    if not isinstance(proto, type(None)):
        if port_src is not None or port_dst is not None:
            if proto == 'tcp':
                rule += ['-p', 'tcp']
            else:
                rule += ['-p', 'udp']

            if port_src is not None:
                rule += ['--sport', str(port_src)]
            if port_dst is not None:
                rule += ['--dport', str(port_dst)]
    rule += ['-j', 'DROP']
    return rule


def _cmd_drop_packets(iface, oface, ip_src, ip_dst, proto, port_src, port_dst, bridge=False):
    if not isinstance(oface, type(None)):
        chain_name = 'FORWARD'
    else:
        chain_name = 'INPUT'

    rule = _cmd_build_drop_packets_rule(iface, oface, ip_src, ip_dst, proto, port_src, port_dst, bridge)
    cmd = ['/sbin/iptables', '-t', 'filter', '-A', chain_name]
    subprocess.call(cmd + rule)


def drop_packets(iface, oface, ip_src, ip_dst, proto, port_src, port_dst, bridge=False):
    if HAS_IPTC:
        _iptc_drop_packets(iface, oface, ip_src, ip_dst, proto, port_src, port_dst, bridge)
    else:
        _cmd_drop_packets(iface, oface, ip_src, ip_dst, proto, port_src, port_dst, bridge)

def _iptc_undrop_packets(iface, oface, ip_src, ip_dst, proto, port_src, port_dst, bridge):
    if not isinstance(oface, type(None)):
        chain_name = 'FORWARD'
    else:
        chain_name = 'INPUT'

    r = _iptc_build_drop_packets_rule(iface, oface, ip_src, ip_dst, proto, port_src, port_dst, bridge)
    c = iptc.Chain(iptc.Table(iptc.Table.FILTER), chain_name)
    c.delete_rule(r)


def _cmd_undrop_packets(iface, oface, ip_src, ip_dst, proto, port_src, port_dst, bridge):
    if not isinstance(oface, type(None)):
        chain_name = 'FORWARD'
    else:
        chain_name = 'INPUT'

    rule = _cmd_build_drop_packets_rule(iface, oface, ip_src, ip_dst, proto, port_src, port_dst, bridge)
    cmd = ['/sbin/iptables', '-t', 'filter', '-D', chain_name]
    subprocess.call(cmd + rule)


def undrop_packets(iface, oface, ip_src, ip_dst, proto, port_src, port_dst, bridge=False):
    if HAS_IPTC:
        _iptc_undrop_packets(iface, oface, ip_src, ip_dst, proto, port_src, port_dst, bridge)
    else:
        _cmd_undrop_packets(iface, oface, ip_src, ip_dst, proto, port_src, port_dst, bridge)

def _iptc_build_packet_extraction_rule(port, queue_num, src_mac=None, dport=False):
    r = iptc.Rule()
    r.set_protocol('tcp')
    if dport:
        r.create_match('tcp').dport = port
    else:
        r.create_match('tcp').sport = port

    if not isinstance(src_mac, type(None)):
        r.create_match('mac').mac_source = src_mac

    r.create_target('NFQUEUE').set_parameter('queue-num', queue_num)
    return r


def _iptc_extract_packets(chain, port, src_mac, queue_num):
    c = iptc.Chain(iptc.Table(iptc.Table.FILTER), chain)  # TODO chain??

    r = _iptc_build_packet_extraction_rule(port, queue_num, src_mac, dport=False)
    c.append_rule(r)
    r = _iptc_build_packet_extraction_rule(port, queue_num, src_mac, dport=True)
    c.append_rule(r)


def _cmd_build_packet_extraction_rule(port, queue_num, src_mac=None, dport=False):
    rule = ['-m', 'tcp']
    if dport:
        rule += ['--dport', str(port)]
    else:
        rule += ['--sport', str(port)]

    if not isinstance(src_mac, type(None)):
        rule += ['-m', 'mac', '--mac-source', src_mac]

    rule += ['-j', 'NFQUEUE', '--queue-num', str(queue_num)]
    return rule


def _cmd_extract_packets(chain, port, src_mac, queue_num):
    cmd = ['/sbin/iptables', '-t', 'filter' '-A', chain]

    rule = _cmd_build_packet_extraction_rule(port, queue_num, src_mac, dport=False)
    subprocess.call(cmd + rule)

    rule = _cmd_build_packet_extraction_rule(port, queue_num, src_mac, dport=True)
    subprocess.call(cmd + rule)


def extract_packets(chain, port, src_mac=None, queue_num=0):
    if HAS_IPTC:
        _iptc_extract_packets(chain, port, src_mac, queue_num)
    else:
        _cmd_extract_packets(chain, port, src_mac, queue_num)


def _iptc_extract_packets_cancel(chain, src_mac, port, queue_num):
    c = iptc.Chain(iptc.Table(iptc.Table.FILTER), chain)

    r = _iptc_build_packet_extraction_rule(port, queue_num, src_mac, dport=False)
    c.delete_rule(r)
    r = _iptc_build_packet_extraction_rule(port, queue_num, src_mac, dport=True)
    c.delete_rule(r)

def _cmd_extract_packets_cancel(chain, src_mac, port, queue_num):
    cmd = ['/sbin/iptables', '-t', 'filter', '-D', chain]

    rule = _cmd_build_packet_extraction_rule(port, queue_num, src_mac, dport=False)
    subprocess.call(cmd + rule)

    rule = _cmd_build_packet_extraction_rule(port, queue_num, src_mac, dport=True)
    subprocess.call(cmd + rule)

def extract_packets_cancel(chain, src_mac, port, queue_num=0):
    if HAS_IPTC:
        _iptc_extract_packets_cancel(chain, src_mac, port, queue_num)
    else:
        _cmd_extract_packets_cancel(chain, src_mac, port, queue_num)