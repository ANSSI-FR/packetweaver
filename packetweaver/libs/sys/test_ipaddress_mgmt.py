import pytest
import ipaddress
import packetweaver.libs.sys.ipaddress_mgmt as ipm


class TestIpAddressMgmt:
    def test_is_a_valid_ip_address(self):
        assert ipm.is_a_valid_ip_address('1.2.3.4') is True
        assert ipm.is_a_valid_ip_address('0.0.0.0') is True
        assert ipm.is_a_valid_ip_address(12) is True
        assert ipm.is_a_valid_ip_address('1.2.3.') is False
        assert ipm.is_a_valid_ip_address('a.2.3.4') is False
        assert ipm.is_a_valid_ip_address('1.2.3.400') is False
        assert ipm.is_a_valid_ip_address([1, 2, 3, 4]) is False
        assert ipm.is_a_valid_ip_address('1.2.3.400/12') is False
        assert ipm.is_a_valid_ip_address('1.2.3.400:80') is False
        assert ipm.is_a_valid_ip_address('1.2.3.400/24:80') is False
        assert ipm.is_a_valid_ip_address('') is False

        assert ipm.is_a_valid_ip_address('1:2:3:4:5:6:7:8') is True
        assert ipm.is_a_valid_ip_address('ab:cd:3:4:5:6:7:8') is True
        assert ipm.is_a_valid_ip_address('1::3:4:5:6:7:8') is True
        assert ipm.is_a_valid_ip_address('1::8') is True
        assert ipm.is_a_valid_ip_address('::1') is True
        assert ipm.is_a_valid_ip_address('::') is True
        assert ipm.is_a_valid_ip_address('01ab:cd:3:4:5:6:7:8') is True
        assert ipm.is_a_valid_ip_address('1ab:cd:3:4:5:6:7:8') is True
        assert ipm.is_a_valid_ip_address('1ab:cd:3:4:5:6:7:8/100') is False
        assert ipm.is_a_valid_ip_address('1:2::6::7:8') is False

        with pytest.raises(TypeError):
            ipm.is_a_valid_ip_address()

    def test_get_network_object(self):
        assert isinstance(ipm.get_network_object('1.2.3.4'),
                          ipaddress.IPv4Network)
        assert isinstance(ipm.get_network_object('1.2.3.4/1'),
                          ipaddress.IPv4Network)
        assert isinstance(ipm.get_network_object('1.2.3.4/0'),
                          ipaddress.IPv4Network)
        assert ipm.get_network_object('1.2.3.4/33') is None
        assert ipm.get_network_object('.2.3.4/33') is None

        assert isinstance(ipm.get_network_object('1:2:3:4:5:6:7:8'),
                          ipaddress.IPv6Network)
        assert isinstance(ipm.get_network_object('1:2:3:4:5:6:7:8/0'),
                          ipaddress.IPv6Network)
        assert ipm.get_network_object('1:2:3:4:5:6:7:8/129') is None

    def test_is_a_valid_prefix(self):
        assert ipm.is_a_valid_prefix('1.2.3.4') is True
        assert ipm.is_a_valid_prefix('1.2.3.4/3') is True
        assert ipm.is_a_valid_prefix('1.2.3.4/33') is False

        assert ipm.is_a_valid_prefix('1:2:3:4:5:6:7:8') is True
        assert ipm.is_a_valid_prefix('1:2:3:4:5:6:7:8/128') is True
        assert ipm.is_a_valid_prefix('1:2:3:4:5:6:7:8/129') is False

        with pytest.raises(TypeError):
            ipm.is_a_valid_prefix()

    # def test_get_ip_count_in_prefix(self):
    #     assert ipm.get_ip_count_in_prefix('1.2.3.4/31') == 1
    #     assert ipm.get_ip_count_in_prefix('1.2.3.4/24') == 255
