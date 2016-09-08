from twisted.web import server, resource
from twisted.internet import reactor

class HelloResource(resource.Resource):
    isLeaf = True
    numberRequests = 0

    def render_GET(self, request):
        self.numberRequests += 1
        request.setHeader("content-type", "text/plain")
        print "%r" %request
        return "I am request #" + str(self.numberRequests) + "\n"

reactor.listenTCP(8000, server.Site(HelloResource()))
reactor.run()
