import ipaddress


def is_a_valid_ip_address(s):
    try:
        ipaddress.ip_address(s)
        return True
    except ValueError:
        return False


def get_network_object(prefix):
    u = prefix
    try:
        return ipaddress.IPv4Network(u, strict=False)
    except (ValueError,
            ipaddress.AddressValueError,
            ipaddress.NetmaskValueError):
        pass
    try:
        return ipaddress.IPv6Network(u, strict=False)
    except (ValueError,
            ipaddress.AddressValueError,
            ipaddress.NetmaskValueError):
        return None


def is_a_valid_prefix(s):
    return s is not None and get_network_object(s) is not None


def get_ip_count_in_prefix(prefix):
    net_obj = get_network_object(prefix)
    assert net_obj is not None
    return net_obj.num_addresses - 2


def get_nth_ip_in_prefix(prefix, n):
    net_obj = get_network_object(prefix)
    assert net_obj is not None
    if isinstance(net_obj.network_address, ipaddress.IPv4Address):
        return str(ipaddress.IPv4Address(int(net_obj.network_address) + n))
    else:
        return str(ipaddress.IPv6Address(int(net_obj.network_address) + n))
