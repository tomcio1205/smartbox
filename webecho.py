# -*- coding: utf-8 -*-
from twisted.protocols import basic
from twisted.internet import protocol, reactor
from binascii import unhexlify
import psycopg2
from socket import inet_aton
from struct import pack

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
			query = "Select ip_adress, port from servers where id = 1"
			query_result = self.database_operation(query, "select")
			ip = query_result[0][0]
			port = query_result[0][1]
			ip_byte = bytearray(inet_aton(str(ip)))
			#port is saved in two bytes, port varaible in example i equal to 8000
			#so port port_byte is write in two bytes, for 8000 is equal to '@\x1f'
			#port_byte[0] = 64 , port_byte[1] = 31
			port_byte = bytearray(pack('h', port))
			# TODO don't know how set 3rd byte
			# for now 3rd byte will be resend
			# TODO for now nothing change in first 3 byte so maybe mask is not necessary?
			#TODO in bytes from 11 to 29 we send information about smartboxes working in current network,
			#this must be done later beacouse i dont know how to get this information
			#64 because its means that next package will be configuration package

			list_of_bytes_send.extend([list_of_bytes[0], list_of_bytes[1], 64,
			                           list_of_bytes[3], ip_byte[0], ip_byte[1], ip_byte[2],
			                           ip_byte[3], port_byte[0], port_byte[1]])
			# list_of_bytes_send is bytearray type which is represented by bytearray(b'\xff\xff')
			# to send only bytes we must convert this array and we get only '\xff\xff'
			self.sendResponse(bytes(list_of_bytes_send))

		if f_key == f_key_ready_for_configuration:
			print "Dobra jestem gotowy na przyjęcie nowej paczki z konfiguracją - dawaj ją!"

			# TODO this query is hardcoded,it must be changed
			query = "Select ip_adress, port from servers where id = 1"
			query_result = self.database_operation(query, "select")
			ip = query_result[0][0]
			port = query_result[0][1]
			ip_byte = bytearray(inet_aton(str(ip)))
			#port is saved in two bytes, port varaible in example i equal to 8000
			#so port port_byte is write in two bytes, for 8000 is equal to '@\x1f'
			#port_byte[0] = 64 , port_byte[1] = 31
			port_byte = bytearray(pack('h', port))
			# TODO don't know how set 3rd byte
			# for now 3rd byte will be resend
			# TODO for now nothing change in first 3 byte so maybe mask is not necessary?
			#TODO in bytes from 11 to 29 we send information about smartboxes working in current network,

			#get first two bytes - smartbox id
			smart_id_hex = data_string_of_bytes[:2]
			#convert id to decimal
			smart_id = int(smart_id_hex.encode('hex'), 16)
			query_network_id = "Select network_id from smartbox_settings where smart_id = %d" % smart_id
			# print smart_id
			network_id = self.database_operation(query_network_id, "select")[0][0]
			query = "Select smart_id, smart_password from smartbox_settings where network_id = %d" % network_id
			all_smartboxes_ids = self.database_operation(query, "select")
			smartboxes_count = len(all_smartboxes_ids)
			# -1 beacuse select return also id of master smartbox
			#128 because its means that this package is the configuration package
			list_of_bytes_send.extend([list_of_bytes[0], list_of_bytes[1], 128, list_of_bytes[3],
			                           ip_byte[0], ip_byte[1], ip_byte[2], ip_byte[3], port_byte[0],
			                           port_byte[1], smartboxes_count-1])

			if all_smartboxes_ids:
				for ids in all_smartboxes_ids:
					next_smart_id = bytearray(pack('h', ids[0]))
					#in this order because first is send high byte
					list_of_bytes_send.extend([next_smart_id[1], next_smart_id[0], int(ids[1])])
			# TODO send sum cntrol
			print "%r" % list_of_bytes_send

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
