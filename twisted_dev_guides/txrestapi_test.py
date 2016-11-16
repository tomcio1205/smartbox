from txrestapi.methods import GET, POST, PUT, ALL
from txrestapi.resource import APIResource
from twisted.web.server import Site
from twisted.web.resource import Resource

from twisted.internet import reactor
from twisted.web.server import Request

class FakeChannel(APIResource):

	@GET('^/(?P<id>[^/]+)/info')
	def get_info(self, request, id):
		return 'Info for id %s' % id
	# def get_callback(self, request):
	# 	return 'GET callback'
	#
	# def post_callback(self, request):
	# 	return 'POST callback'

api = FakeChannel()
site = Site(api, timeout=None)
# api.register('GET', '^/path/to/method', x.get_callback)
# api.register('GET', '^/path/to', x.post_callback)
reactor.listenTCP(8800, site)
reactor.run()
