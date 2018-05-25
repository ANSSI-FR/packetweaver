import packetweaver.libs.six as six
try:
    import ipaddress

    def is_a_valid_ip_address(s):
        try:
            if six.PY2:
                ipaddress.ip_address(s.decode("utf8"))
            elif six.PY3:
                ipaddress.ip_address(s)
            else:
                print("Unknown python v. while checking IP option validity with ipaddress")
            return True
        except:
            return False


    def get_network_object(prefix):
        if six.PY2:
            u = prefix.decode("utf8")
        elif six.PY3:
            u = prefix
        else:
            print("Unknown python v. while checking network object validity with ipaddress")
        try:
            return ipaddress.IPv4Network(u, strict=False)
        except (ValueError, ipaddress.AddressValueError, ipaddress.NetmaskValueError):
            pass
        try:
            return ipaddress.IPv6Network(u, strict=False)
        except (ValueError, ipaddress.AddressValueError, ipaddress.NetmaskValueError):
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

except ImportError:
    print("Cannot verify IP addresses format! Please install ipaddress or use python 3")

    def is_a_valid_ip_address(s):
        return True

    def is_a_valid_prefix(s):
        return True