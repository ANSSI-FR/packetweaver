

class StatusItem(object):
    """ Upper class of all Status classes

    These status will be used in abilities to quantify
    the status a specific property.
    """
    pass


class Reliability(StatusItem):
    """ Defines several level of reliability of an
     ability source code.

    NOT_WORKING: code in construction
    UNSTABLE: works at least once
    TESTED: several tests have been performed to challenge its reliability
    RELIABLE: higher than TESTED, has been tested in several environments
    INCOMPLETE: all advertised functionality have not been implemented
    """
    NOT_WORKING = "Not working"
    UNSTABLE = "Unstable"
    TESTED = "Tested"
    RELIABLE = "Reliable"
    INCOMPLETE = "Incomplete"


class Tag(StatusItem):
    """ Defines several tags to categorize a ability by its load

    INTRUSIVE: intrusive network actions are performed
    SCAN: performs network scans
    EXAMPLE: demonstrate a framework functionality
    OFFLINE: do not generate traffic
    THREADED: make use of threaded abilities
    TCP_STACK_L1: make use of protocols from the 1st OSI model level
    TCP_STACK_L2: make use of protocols from the 1nd OSI model level
    TCP_STACK_L3: make use of protocols from the 1rd OSI model level
    TCP_STACK_L4: make use of protocols from the 1th OSI model level
    TCP_STACK_L5: make use of protocols from the 1th OSI model level
    ICS = "ICS": address industrial control system issues
    UTest: used by unit tests
    """
    INTRUSIVE = "Intrusive"
    SCAN = "Scan"
    EXAMPLE = "Example"
    OFFLINE = "Offline"
    THREADED = "Threaded"
    TCP_STACK_L1 = "Physical_Layer"
    TCP_STACK_L2 = "Data Link_Layer"
    TCP_STACK_L3 = "Network_Layer"
    TCP_STACK_L4 = "Transport_Layer"
    TCP_STACK_L5 = "Application_Layer"
    ICS = "ICS"
    UTEST = "UTest"
    DNS = "DNS"


class OptNames(object):
    """ Defines tags to specify default names to frequently used ability
        parameter types

    MAC_SRC: an Ethernet source MAC (Media Access Control) address
    MAC_DST: an Ethernet destination MAC
    IP_SRC: a IP (Internet Protocol) source address
    IP_DST: a IP (Internet Protocol) destination address
    PORT_SRC: a TCP(Transmission Control Protocol)/UDP(User Datagram Protocol)
        source port
    PORT_DST: a TCP/UDP destination port
    INPUT_INTERFACE: name of the host network interface to be used to receive
        network traffic
    OUTPUT_INTERFACE: name of the host network interface to be used to send
        traffic
    L4PROTOCOL: a OSI level 4 protocol over IP, used to abstract for example
        the use of TCP or UDP
    CALLBACK: to specify a callback parameter
    INPUT_PIPE: to name an input communication pipe
    OUTPUT_PIPE: to name an output communication pipe
    PATH_DST: to specify a path (file or directory) to write a specific content
    PATH_SRC: to specify a path (file or directory) that will be use to read
        information
    """
    MAC_SRC = 'mac_src'
    MAC_DST = 'mac_dst'
    IP_SRC = 'ip_src'
    IP_DST = 'ip_dst'
    PORT_SRC = 'port_src'
    PORT_DST = 'port_dst'
    INPUT_INTERFACE = 'interface'
    OUTPUT_INTERFACE = 'outerface'
    L4PROTOCOL = 'protocol'
    CALLBACK = 'callback'
    INPUT_PIPE = 'in_pipe'
    OUTPUT_PIPE = 'out_pipe'
    PATH_DST = 'path_dst'
    PATH_SRC = 'path_src'


class AbilityType(object):
    """ Defines the type of a Module (i.e ability)

    STANDALONE: the ability is standalone and can thus be called directly by
        the framework
    COMPONENT: the ability cannot be called by the user and has to be used by
        another ability
    """
    STANDALONE = "Standalone"
    COMPONENT = "Component"
