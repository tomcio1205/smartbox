from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet import reactor, endpoints
from twisted.web.static import File

root = Resource()
root.putChild("foo", File("/tmp"))
root.putChild("bar", File("/home"))
root.putChild("baz", File("/opt"))

factory = Site(root)
endpoint = endpoints.TCP4ServerEndpoint(reactor, 8880)
endpoint.listen(factory)
reactor.run()