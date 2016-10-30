import httplib
import time
import sys
from multiprocessing.dummy import Pool as ThreadPool
import threading
# params = urllib.urlencode({'@number': 12524, '@type': 'issue', '@action': 'show'})
threads_number = 2
latency_array = []

program_start = time.time()
f = open('http_latency1.txt', 'a')
f.write("\nNEXT TEST FOR MEASURE REQUEST TIME (%d THREADS)\n\n" % threads_number)
f.close()


def httpClient(threadName):
	headers = {"Content-type": "application/x-www-form-urlencoded",
	           "Accept": "text/plain"}
	data = '\x01\xc3\x01\x90\x04\xe2\xe6\x01\xc4\x01\xff\x04\xe2\xe6\x01\xc5\x01\xff\x04\xe2\x01\x8a\xe4'
	conn = httplib.HTTPConnection("127.0.0.1", 8880)
	# while True:
	while True:
		f = open('http_latency1.txt', 'a')
		start = time.time()
		conn.request("POST", "/smartbox", data, headers)
		response = conn.getresponse()
		# data = response.read()
		print threadName, response.status, response.reason
		print response.read().split(':p', 1)[0]
		conn.close()
		end = time.time()
		f.write("Thread number %s : Request latency: %.4f s \n" % (threadName, (end - start)))
		time.sleep(5)
		f.close()
		latency_array.append((end - start))
		program_end = time.time()
		if (program_end - program_start) > 40:
		# if (program_end - program_start) > 1:
			# print sum(latency_array)
			time.sleep(1)
			f = open('http_latency1.txt', 'a')
			f.write("AVERAGE TIME REQUEST FOR THREAD NUMBER %s: %.4f\n" % (threadName, sum(latency_array)/len(latency_array)))
			f.close()
			sys.exit(0)


thread_list = []
for i in range(1, threads_number):
	name = "Thread - %d: " % i
	t = threading.Thread(target=httpClient, name=name, args=(name,))
	thread_list.append(t)
for thread in thread_list:
	thread.start()


