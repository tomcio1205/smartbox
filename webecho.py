# -*- coding: utf-8 -*-
from twisted.protocols import basic
from twisted.internet import protocol, reactor
from binascii import unhexlify
import psycopg2
from socket import inet_aton

# bit mask to check if memory in smartbox is empty
f_key_empty_memory = 128
# bit mask - smartbox saying that it is ready for configuration package
f_key_ready_for_configuration = 64
# bit mask - smartbox saying that it is report package
f_key_report = 16
# bit mask - smartbox saying that server resend wrong pin
f_key_wrong_pin = 8
# bit mask - smartbox saying that something draws current
f_key_draw_current = 4
# bit mask - smartbox saying that something cause alarm
f_key_alarm = 2
# bit mask - output state of smartbox
f_key_output_state = 1


class HTTPEchoProtocol(basic.LineReceiver):
	def __init__(self):
		self.lines = []

	def lineReceived(self, line):
		self.lines.append(line)
		# print line
		self.f_key_interpretation(line)
		if not line:
			self.sendResponse()

	def sendResponse(self, send_package):
		# self.sendLine("HTTP/1.1 200 OK")
		# self.sendLine("")
		responseBody = "Return package : %r\r\n" % send_package
		self.transport.write(responseBody)

	# self.transport.loseConnection()

	def f_key_interpretation(self, data):
		# unfortunately python replace escape character \x with \\x so below code convert received string
		data_replace_backslash = data.replace("\\x", "")
		# Convert the hex string to string of bytes.
		data_string_of_bytes = unhexlify(data_replace_backslash)
		list_of_bytes = bytearray(data_string_of_bytes)
		# print "%r" %list_of_bytes
		f_key = list_of_bytes[2]
		list_of_bytes_send = []
		# print f_key
		# TODO this will work only if one bit will be set in f_key byte
		if f_key == f_key_empty_memory:
			print "Mam pustą pamięć proszę o paczkę konfiguracji"
			# TODO this query is hardcoded,it must be changed
			ip_query = "Select ip_adress from servers where id = 1"
			ip = self.database_operation(ip_query, "select")[0][0]
			ip_byte = bytearray(inet_aton(str(ip)))
			print "%r" % ip_byte
			# TODO don't know how set 3rd byte
			# for now 3rd byte will be resend
			# TODO for now nothing change in first 3 byte so maybe mask is not necessary?
			list_of_bytes_send.extend([list_of_bytes[0], list_of_bytes[1], list_of_bytes[2],
			                           list_of_bytes[3], ip_byte[0], ip_byte[1], ip_byte[2],
			                           ip_byte[3]])
			# list_of_bytes_send is bytearray type which is represented by bytearray(b'\xff\xff')
			# to send only bytes we must convert this array and we get only '\xff\xff'
			self.sendResponse(bytes(list_of_bytes_send))
		if f_key == f_key_ready_for_configuration:
			print "Dobra jestem gotowy na przyjęcie nowej paczki z konfiguracją - dawaj ją!"
		if f_key == f_key_report:
			print "Ta paczka to raport na temat sieci i ostatniego połaczenia"
		if f_key == f_key_wrong_pin:
			print "W naszej poprzedniej rozmowie podałeś błędny PIN"
		if f_key == f_key_draw_current:
			print "Coś pobiera prąd w mniejszym lub większym stopniu prąd ale jednak"
		if f_key == f_key_alarm:
			print "Zaistniał alarm z przeciążenia/zwarcie gniazdka"
		if f_key == f_key_output_state:
			print "Stan wyjścia obecny"

	def database_operation(self, query, query_type):
		# database connection
		conn = psycopg2.connect(database="smartbox", user="postgres", password="postgres", host="127.0.0.1",
		                        port="5432")
		cur = conn.cursor()
		cur.execute(query)
		rows = cur.fetchall()
		return rows
		conn.close()


class HTTPEchoFactory(protocol.ServerFactory):
	def buildProtocol(self, addr):
		return HTTPEchoProtocol()


# class MyClass(HTTPEchoProtocol):
# 	def __init__(self, line):
# 		self.f_key_interpretation(int(line))
#
# 	def f_key_interpretation(self, line):
# 		# f_key_mask = 111111110000000000000000
# 		f_key_mask = 16711680
# 		f_key = int(line) & f_key_mask
# 		#TODO this will work only if one bit will be set in f_key byte
# 		if f_key == f_key_empty_memory:
# 			print "Mam pustą pamięć proszę o paczkę konfiguracji"
# 		if f_key == f_key_ready_for_configuration:
# 			print "Dobra jestem gotowy na przyjęcie nowej paczki z konfiguracją - dawaj ją!"
# 		if f_key == f_key_report:
# 			print "Ta paczka to raport na temat sieci i ostatniego połaczenia"
# 		if f_key == f_key_wrong_pin:
# 			print "W naszej poprzedniej rozmowie podałeś błędny PIN"
# 		if f_key == f_key_draw_current:
# 			print "Coś pobiera prąd w mniejszym lub większym stopniu prąd ale jednak"
# 		if f_key == f_key_alarm:
# 			print "Zaistniał alarm z przeciążenia/zwarcie gniazdka"
# 		if f_key == f_key_output_state:
# 			print "Stan wyjścia obecny"

reactor.listenTCP(8000, HTTPEchoFactory())
reactor.run()
