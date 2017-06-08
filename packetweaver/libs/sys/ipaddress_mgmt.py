try:
    import ipaddress

    def is_a_valid_ip_address(s):
        try:
            ipaddress.ip_address(s.decode("utf8"))
            return True
        except:
            return False


    def get_network_object(prefix):
        u = prefix.decode('utf8')
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
    try:
        import netaddr

        def is_a_valid_ip_address(s):
            try:
                netaddr.IPAddress(s)
                return True
            except:
                return False


        def is_a_valid_prefix(s):
            if s is None:
                return False
            try:
                p = netaddr.IPNetwork(s)
                return True
            except netaddr.core.AddrFormatError:
                return False


        def get_ip_count_in_prefix(prefix):
            net_obj = netaddr.IPNetwork(prefix)
            return net_obj.size - 2

        def get_nth_ip_in_prefix(prefix, n):
            return str(netaddr.IPAddress(int(netaddr.IPNetwork(prefix).first) + n + 1))

    except ImportError:
        print("Cannot verify IP addresses format! Please install either Python ipaddress or netaddr modules")

        def is_a_valid_ip_address(s):
            return True

        def is_a_valid_prefix(s):
            return True