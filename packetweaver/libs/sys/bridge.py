import copy
try:
    import pyroute2
    HAS_PYROUTE2 = True
except ImportError:
    HAS_PYROUTE2 = False


def in_bridge(ifname):
    with pyroute2.IPDB() as ipdb:
        for iface in ipdb.interfaces:
            if (
                hasattr(iface, 'kind') and iface.kind == 'bridge'
                and hasattr(iface, 'ports') and hasattr(iface, 'ifname')
            ):
                for port in iface.ports:
                    if port.ifname == ifname:
                        return iface.ifname
    return None


def is_bridge(ifname):
    with pyroute2.IPDB() as ipdb:
        return hasattr(ipdb.interfaces[ifname], 'kind') and ipdb.interfaces[ifname].kind == 'bridge'


def bridge_iface_together(*args, **kwargs):
    """
    :param args: list of interface names to add to the bridge
    :param kwargs: keyword argument "bridge" allows the caller to specify to which bridge the interfaces must be added. If not specified, a new bridge is created, and named
    :return:
    """
    with pyroute2.IPDB() as ipdb:
        name = ""
        if 'bridge' in kwargs and not isinstance(kwargs['bridge'], type(None)):
            if kwargs['bridge'] in ipdb.interfaces:
                br = ipdb.interfaces[kwargs['bridge']]
            else:
                name = kwargs['bridge']
        else:
            # Get a new bridge identifier
            l = ([int(x[len('pwbr'):]) for x in ipdb.interfaces.keys() if isinstance(x,str) and x.startswith('pwbr')])
            if len(l) == 0:
                i = 0
            else:
                i = max(l) + 1
            name = 'pwbr{}'.format(i)

        if len(name) > 0:
            br = ipdb.create(kind='bridge', ifname=name)
            br.up()
            ipdb.commit()

        # Create the new bridge and add the two interfaces in it
        for a in args:
            br.add_port(a)

        ipdb.commit()
        return br.ifname


def unbridge(brif):
    with pyroute2.IPDB() as ipdb:
        ports = copy.copy(ipdb.interfaces[brif].ports)
        ipdb.interfaces[brif].down()
        ipdb.commit()
        ipdb.interfaces[brif].remove()
        ipdb.commit()
        for port in ports:
            ipdb.interfaces[port].up()
        ipdb.commit()


def create_dummy_if(ifname, ipaddr=None):
    with pyroute2.IPDB() as ipdb:
        ipdb.create(kind='dummy', ifname=ifname)
        if not isinstance(ipaddr, type(None)):
            ipdb.interfaces[ifname].ipaddr = ipaddr
        ipdb.commit()


remove_dummy_if = unbridge


# if __name__=='__main__':
#     bridge_iface_together('tititoto', 'tititoto2', 'tititoto3')
#     bridge_iface_together('tititoto3', 'tititoto4')
#     unbridge('pwbr0')
#     bridge_iface_together('tititoto', 'tititoto2')

