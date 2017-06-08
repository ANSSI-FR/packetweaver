# coding: utf8
import subprocess
import os


def enable_ip_forwarding():
    os_name = os.uname()[0]
    if os_name == 'Linux':
        subprocess.call(["sysctl -w net.ipv4.ip_forward=1"], shell=True)
    elif os_name == 'FreeBSD':
        subprocess.call(["sysctl -w net.inet.ip.forwarding=1"], shell=True)
    else:
        raise Exception()


def disable_ip_forwarding():
    os_name = os.uname()[0]
    if os_name == 'Linux':
        subprocess.call(["sysctl -w net.ipv4.ip_forward=0"], shell=True)
    elif os_name == 'FreeBSD':
        subprocess.call(["sysctl -w net.inet.ip.forwarding=0"], shell=True)
    else:
        raise Exception('Unsupported OS {}'.format(os_name))

def is_ip_forwarding_active():
    """
    :return: Boolean
    """

    os_name = os.uname()[0]
    if os_name == 'Linux':
        proc = subprocess.Popen(["sysctl -b net.ipv4.ip_forward"], stdout=subprocess.PIPE, shell=True)
    elif os_name == 'FreeBSD':
        proc = subprocess.Popen(["sysctl -b net.inet.ip.forwarding"], stdout=subprocess.PIPE, shell=True)
    else:
        raise Exception('Unsupported OS: {}'.format(os_name))

    (out, err) = proc.communicate()
    if out == "1":
        return True
    elif out == "0":
        return False
    else:
        return None
