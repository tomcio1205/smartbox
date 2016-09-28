# -*- coding: utf-8 -*-

import json
import psycopg2
from socket import inet_aton
from struct import pack

from PyCRC.CRCCCITT import CRCCCITT
from twisted.internet import reactor, endpoints
from twisted.web.resource import Resource
from twisted.web.server import Site

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


class ApiPage(Resource):
	# def render_GET(self, request):
	#     return '<html><body><form method="POST"><input name="the-field" type="text" /></form></body></html>'

	def render_POST(self, request):
		x = json.loads(request.content.read())
		print x
		request.write('<html><body>You submitted: %r</body></html>' % x)  # (cgi.escape(request.content.read()),)

	# request.finish()


class SmartboxPage(Resource):
	def render_POST(self, request):
		data = request.content.read()
		self.handling_samrtbox_data(request, data)

	def render_GET(self, request):
		print "%r" % request.content.read()
		request.write("cccccccccccccccc")

	def handling_samrtbox_data(self, request, data):
		list_of_bytes = [ord(my_byte) for my_byte in data]
		print "%r" % data
		f_key = list_of_bytes[2]
		list_of_bytes_send = []
		# get id of currently communicating smartbox
		my_smart_id_hex = ''.join('{:02x}'.format(x) for x in list_of_bytes[:2])
		my_smart_id = int(my_smart_id_hex, 16)
		# print f_key
		# TODO this will work only if one bit will be set in f_key byte
		# first we must check sum control
		# sum_of_bytes_to_calc_sum_control = sum(list_of_bytes[:-2])
		checksum = CRCCCITT().calculate(data[:-2])
		receive_sum_control_hex = ''.join('{:02x}'.format(x) for x in list_of_bytes[-2:])
		receive_sum_control = int(receive_sum_control_hex, 16)
		db_operation = DatabaseCommunication()

		if checksum == receive_sum_control:
			print "Suma kontrolna zweryfikowana poprawnie"
		else:
			print "Sumy kontrolne różne, nie rozpatruję paczki \n"
			return 0

		if f_key == f_key_output_state:
			count_smartboxes = (len(list_of_bytes) - 2) / 7
			print "Stan wyjścia obecny"
			for smartbox in range(count_smartboxes):
				smart_id_hex = ''.join(chr(bt) for bt in list_of_bytes[smartbox * 7:smartbox * 7 + 2])
				# convert id to decimal
				smart_id = int(smart_id_hex.encode('hex'), 16)
				# 5 and 6 bytes represent power consumption of electric socket which master smartbox is connected to
				power_consumption_hex = ''.join(chr(bt) for bt in list_of_bytes[smartbox * 7 + 4:smartbox * 7 + 6])
				# convert power consumption to decimal
				power_consumption = int(power_consumption_hex.encode('hex'), 16)

				# 7 bytes represent voltage of electric socket which master smartbox is connected to
				# current_voltage_hex = chr(list_of_bytes[smartbox*7+6])
				# convert voltage to decimal
				# current_voltage = int(current_voltage_hex.encode('hex'), 16)

				current_voltage = list_of_bytes[smartbox * 7 + 6]

				print "My smart id: %d" % smart_id
				print "Power consumption: %d mA/s" % power_consumption
				print "Voltage of electrical socket: %d V" % current_voltage

				query = "INSERT INTO device_measurement(deviceid, powerconsumption, socketvoltage) VALUES(%d, %d, %d)" % (smart_id, power_consumption, current_voltage)
				db_operation.update_operation(query)
		# build package which will be sending
		# TODO what will be send?
		list_of_bytes_send.extend([list_of_bytes[0], list_of_bytes[1], 128, list_of_bytes[3], list_of_bytes[4],
		                           list_of_bytes[5], 128, list_of_bytes[6]])
		# sending bytes(list_of_bytes_send) and reading in smartbox with     Serial.println(line)->[1, 244, 255]
		# Serial.println(line[4]) -> 2 we get single sign from string
		print "%r" % ''.join(str(bytearray(list_of_bytes_send)))
		request.write(''.join(str(bytearray(list_of_bytes_send))))

		if f_key == f_key_wrong_pin:
			print "W naszej poprzedniej rozmowie podałeś błędny PIN"

		if f_key == f_key_draw_current:
			print "Coś pobiera prąd w mniejszym lub większym stopniu prąd ale jednak"

		if f_key == f_key_alarm:
			print "Zaistniał alarm z przeciążenia/zwarcie gniazdka"

		if f_key == f_key_report:
			# \x01\xc3\x10\xff\x04\xe2\xe6\x01\xc4\x01\xff\x04\xe2\xe6\x01\xc5\x01\xff\x04\xe2\xe6\xff\xff
			print "Ta paczka to raport na temat sieci i ostatniego połaczenia"

		if f_key == f_key_ready_for_configuration:
			# \x01\xc3\x40\xff\x04\xe2

			print "Dobra jestem gotowy na przyjęcie nowej paczki z konfiguracją - dawaj ją!"

			# TODO this query is hardcoded,it must be changed
			query = "Select ip_adress, port from servers where id = 1"
			query_result = db_operation.select_operation(query)
			# query_result = self.database_operation(query, "select")
			ip = query_result[0][0]
			port = query_result[0][1]
			ip_byte = bytearray(inet_aton(str(ip)))
			# port is saved in two bytes, port varaible in example i equal to 8000
			# so port port_byte is write in two bytes, for 8000 is equal to '@\x1f'
			# port_byte[0] = 64 , port_byte[1] = 31
			port_byte = bytearray(pack('h', port))
			# TODO don't know how set 3rd byte
			# for now 3rd byte will be resend
			# TODO for now nothing change in first 3 byte so maybe mask is not necessary?
			# TODO in bytes from 11 to 29 we send information about smartboxes working in current network,

			# get first two bytes - smartbox id
			smart_id_hex = ''.join(chr(bt) for bt in list_of_bytes[:2])

			# convert id to decimal
			smart_id = int(smart_id_hex.encode('hex'), 16)
			query_network_id = "Select network_id from smartbox_settings where smart_id = %d" % smart_id
			# print smart_id
			network_id = db_operation.select_operation(query_network_id)[0][0]
			# network_id = self.database_operation(query_network_id, "select")[0][0]
			query = "Select smart_id, smart_password from smartbox_settings where network_id = %d" % network_id
			all_smartboxes_ids = db_operation.select_operation(query)
			smartboxes_count = len(all_smartboxes_ids)
			# -1 beacuse select return also id of master smartbox
			# 128 because its means that this package is the configuration package
			list_of_bytes_send.extend([list_of_bytes[0], list_of_bytes[1], 128, list_of_bytes[3], ip_byte[0],
			                           ip_byte[1], ip_byte[2], ip_byte[3], port_byte[0], port_byte[1],
			                           smartboxes_count - 1])

		if f_key == f_key_empty_memory:
			print "Mam pustą pamięć proszę o paczkę konfiguracji"

			# TODO this query is hardcoded,it must be changed
			query = "Select ip_adress, port from servers where id = 1"
			# query_result = self.database_operation(query, "select")
			query_result = db_operation.select_operation(query)
			ip = query_result[0][0]
			port = query_result[0][1]
			ip_byte = bytearray(inet_aton(str(ip)))
			# port is saved in two bytes, port varaible in example i equal to 8000
			# so port port_byte is write in two bytes, for 8000 is equal to '@\x1f'
			# port_byte[0] = 64 , port_byte[1] = 31
			port_byte = bytearray(pack('h', port))
			# TODO don't know how set 3rd byte
			# for now 3rd byte will be resend
			# TODO for now nothing change in first 3 byte so maybe mask is not necessary?
			# TODO in bytes from 11 to 29 we send information about smartboxes working in current network,
			# this must be done later beacouse i dont know how to get this information
			# 64 because its means that next package will be configuration package

			list_of_bytes_send.extend([list_of_bytes[0], list_of_bytes[1], 64,
			                           list_of_bytes[3], ip_byte[0], ip_byte[1], ip_byte[2],
			                           ip_byte[3], port_byte[0], port_byte[1]])
			# list_of_bytes_send is bytearray type which is represented by bytearray(b'\xff\xff')
			# to send only bytes we must convert this array and we get only '\xff\xff'
			self.sendResponse(bytes(list_of_bytes_send))

		# def database_operation(self, query, query_type):
		# 	# database connection
		# 	conn = psycopg2.connect(database="smartbox", user="postgres", password="postgres", host="127.0.0.1",
		# 	                        port="5432")
		# 	cur = conn.cursor()
		# 	cur.execute(query)
		# 	rows = cur.fetchall()
		# 	return rows
		# 	conn.close()


class DatabaseCommunication:
	def __init__(self):
		# global conn
		self.conn = psycopg2.connect(database="smartbox_database", user="postgres", password="postgres", host="127.0.0.1",
		                             port="5432")

	def select_operation(self, query):
		# database connection
		cur = self.conn.cursor()
		cur.execute(query)
		rows = cur.fetchall()
		self.conn.close()
		return rows

	def update_operation(self, query):
		# database connection
		cur = self.conn.cursor()
		cur.execute(query)

		self.conn.commit()
		# self.conn.close()

root = Resource()
root.putChild("api", ApiPage())
root.putChild("smartbox", SmartboxPage())
factory = Site(root)
endpoint = endpoints.TCP4ServerEndpoint(reactor, 8880)
endpoint.listen(factory)
reactor.run()
