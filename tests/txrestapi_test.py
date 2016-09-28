from txrestapi.resource import APIResource



from twisted.web.server import Site, Request
from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import Protocol, Factory


class FakeChannel(object):
	transport = None

# class Echo(Protocol):
#
#     def __init__(self):
#         self.lines = []

# class Protocol(Protocol)

# class HTTPEchoProtocol(basic.LineReceiver):
# 	def __init__(self):
# 		self.lines = []
#
# 	def lineReceived(self, line):
# 		self.lines.append(line)
# 		# print line
# 		self.f_key_interpretation(line)
# 		if not line:
# 			self.sendResponse()


def makeRequest(method, path):
	req = Request(FakeChannel(), None)
	req.prepath = req.postpath = None
	req.method = method
	req.path = path
	resource = site.getChildWithDefault(path, req)
	return resource.render(req)


def get_callback(request):
	print request
	return 'GET callback'


def post_callback(request):
	# x = LineReceiver()
	# print x.dataReceived()
	# HTTPEchoProtocol()
	return 'POST callback'


def default_callback(request):
	return 'Default callback'


def get_info(request, id):
	return 'Information for id %s' % id

api = APIResource()
api.register('GET', '^/get', get_callback)
api.register('POST', '^/post', post_callback)
# api.register('GET', '^/.*$', default_callback)
# api.register('ALL', '^/.*$', default_callback)
api.register('GET', '/(?P<id>[^/]+)/info$', get_info)

site = Factory(api, timeout=None)

reactor.listenTCP(8000, site)
reactor.run()
