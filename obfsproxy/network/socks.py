from twisted.protocols import socks
from twisted.internet.protocol import Protocol, Factory, ClientFactory

import obfsproxy.common.log as log
import obfsproxy.network.network as network

class MySOCKSv4Outgoing(socks.SOCKSv4Outgoing, object):
    """
    Represents a downstream connection from the SOCKS server to the
    destination.

    It monkey-patches socks.SOCKSv4Outgoing, because we need to pass
    our data to the pluggable transport before proxying them
    (Twisted's socks module did not support that).

    Attributes:
    circuit: The circuit this connection belongs to.
    buffer: Buffer that holds data that can't be proxied right
            away. This can happen because the circuit is not yet
            complete, or because the pluggable transport needs more
            data before deciding what to do.
    """

    def __init__(self, socksProtocol):
        """
        Constructor.

        'socksProtocol' is a 'SOCKSv4Protocol' object.
        """

        self.circuit = socksProtocol.circuit
        self.buffer = ''

        self.name = "socks_down_%s" % hex(id(self))

        return super(MySOCKSv4Outgoing, self).__init__(socksProtocol)

    def dataReceived(self, data):
        log.debug("%s: Received %d bytes:\n%s" \
                  % (self.name, len(data), str(data)))

        assert(self.circuit.circuitIsReady()) # XXX Is this always true?

        self.buffer = self.circuit.dataReceived(self.buffer + data, self)

# Monkey patches socks.SOCKSv4Outgoing with our own class.
socks.SOCKSv4Outgoing = MySOCKSv4Outgoing

class SOCKSv4Protocol(socks.SOCKSv4):
    """
    Represents an upstream connection from a SOCKS client to our SOCKS
    server.

    It overrides socks.SOCKSv4 because py-obfsproxy's connections need
    to have a circuit and obfuscate traffic before proxying it.
    """

    def __init__(self, circuit):
        self.circuit = circuit
        self.buffer = ''

        self.name = "socks_up_%s" % hex(id(self))

        return socks.SOCKSv4.__init__(self)

    def dataReceived(self, data):
        """
        Received some 'data'. They might be SOCKS handshake data, or
        actual upstream traffic. Figure out what it is and either
        complete the SOCKS handshake or proxy the traffic.
        """

        # SOCKS handshake not completed yet: let the overriden socks
        # module complete the handshake.
        if not self.otherConn:
            log.debug("%s: Received SOCKS handshake data." % self.name)
            return socks.SOCKSv4.dataReceived(self, data)

        log.debug("%s: Received %d bytes:\n%s" \
                  % (self.name, len(data), str(data)))

        assert(self.otherConn)

        if not self.circuit.circuitIsReady():
            self.circuit.setDownstreamConnection(self.otherConn)
            self.circuit.setUpstreamConnection(self)

        self.buffer = self.circuit.dataReceived(self.buffer + data, self)

    def connectionLost(self, reason):
        log.info("%s: Connection was lost (%s)." % (self.name, reason.getErrorMessage()))
        self.circuit.close()

    def connectionFailed(self, reason):
        log.info("%s: Connection failed to connect (%s)." % (self.name, reason.getErrorMessage()))
        self.circuit.close()

class SOCKSv4Factory(Factory):
    """
    A SOCKSv4 factory.
    """

    def __init__(self, transport):
        # XXX self.logging = log
        self.transport = transport
        self.circuits = []

        self.name = "socks_fact_%s" % hex(id(self))

    def startFactory(self):
        log.info("%s: Starting up SOCKS server factory." % self.name)

    def buildProtocol(self, addr):
        log.info("%s: New connection." % self.name)

        circuit = network.Circuit(self.transport)
        self.circuits.append(circuit)

        return SOCKSv4Protocol(circuit)
