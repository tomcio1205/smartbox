import httplib
import time
from multiprocessing.dummy import Pool as ThreadPool
import threading
# params = urllib.urlencode({'@number': 12524, '@type': 'issue', '@action': 'show'})


def httpClient(threadName):
	headers = {"Content-type": "application/x-www-form-urlencoded",
	           "Accept": "text/plain"}
	data = '\x01\xc3\x01\x90\x04\xe2\xe6\x01\xc4\x01\xff\x04\xe2\xe6\x01\xc5\x01\xff\x04\xe2\x01\x8a\xe4'
	conn = httplib.HTTPConnection("localhost", 8880)
	# while True:
	while True:
		conn.request("POST", "/smartbox", data, headers)
		response = conn.getresponse()
		# data = response.read()
		print threadName, response.status, response.reason
		print response.read().split(':p', 1)[0]
		conn.close()
		time.sleep(5)

thread_list = []
for i in range(1, 10):
	name = "Thread - %d: " % i
	t = threading.Thread(target=httpClient, name=name, args=(name,))
	thread_list.append(t)
for thread in thread_list:
	thread.start()
