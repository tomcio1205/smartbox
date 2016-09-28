from twisted.protocols import basic
from twisted.internet import protocol, reactor
import json


class HTTPEchoProtocol(basic.LineReceiver):
    def __init__(self):
        self.lines = []

    def lineReceived(self, line):
        self.lines.append(line)
        x = json.loads(self._buffer)
        if not line:
            self.sendResponse()
    def sendResponse(self):
        self.sendLine("HTTP/1.1 200 OK")
        self.sendLine("")
        responseBody = "You said:\r\n\r\n" + "\r\n".join(self.lines)
        self.transport.write(responseBody)
        self.transport.loseConnection()


class HTTPEchoFactory(protocol.ServerFactory):
    def buildProtocol(self, addr):
        return HTTPEchoProtocol()


reactor.listenTCP(8000, HTTPEchoFactory())
reactor.run()