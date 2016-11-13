import httplib

# params = urllib.urlencode({'@number': 12524, '@type': 'issue', '@action': 'show'})


def httpClient():
	headers = {"Content-type": "application/x-www-form-urlencoded",
	           "Accept": "text/plain"}
	# data = '\x01\xc3\x01\x04\xe2\x01\xc4\x01\x04\xe2\x01\xc5\x01\x04\xe2\x8a\xe4'
	data = '{"data":[1,195,128,229,191]}'
	conn = httplib.HTTPConnection("192.168.2.107", 8880)
	conn.request("POST", "/configuration", data, headers)
	response = conn.getresponse()
	# data = response.read()
	print response.status, response.reason
	print response.read().split(':p', 1)[0]
	conn.close()


if __name__ == "__main__":
	httpClient()