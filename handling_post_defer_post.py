# -*- coding: utf-8 -*-

import json
import psycopg2
from socket import inet_aton
from struct import pack

from PyCRC.CRCCCITT import CRCCCITT
from twisted.internet import reactor, endpoints
from twisted.web.resource import Resource
from twisted.web.server import Site, NOT_DONE_YET
from twisted.application import service
from twisted.internet.task import deferLater

# from txpostgres import  txpostgres

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
	def render_GET(self, request):
		""" Function to handling GET method from api """
		return '<html><body><form method="POST"><input name="the-field" type="text" /></form></body></html>'

	def render_POST(self, request):
		""" Function to handling POST method from api
            App communicate with server by sending json.
            This function get necessary data from json
            and commit to database """
		data = json.loads(request.content.read())
		db_operation = DatabaseCommunication()
		comma = 0
		query = "UPDATE device SET "

		if 'ison' in data:
			query += "ison = '%s' " % data['ison']
			comma += 1

		if 'should_reset' in data:
			if comma:
				query += ", "
			query += "should_reset = '%s' " % data['should_reset']

		query += "WHERE id = %s" % data['smart_id']
		db_operation.insert_operation(query)

		request.write('<html><body>You submitted: %r</body></html>' % data)

	# request.finish()


class SmartboxConfiguration(Resource):
	def render_POST(self, request):
		data = json.loads(request.content.read())
		print "Configurtion package: %r" % data
		d = deferLater(reactor, 0.01, lambda: request)
		d.addCallback(self.handling_configuration_data, data)

		return NOT_DONE_YET
		# self.handling_configuration_data(request, data)

	def handling_configuration_data(self, request, data):
		list_of_bytes_send = []
		list_of_bytes = data['data']
		f_key = list_of_bytes[2]

		if f_key != 128:
			print "Wrong f_key"
		else:
			checksum = CRCCCITT().calculate("".join(map(chr, list_of_bytes[:-2])))
			receive_sum_control_hex = ''.join('{:02x}'.format(x) for x in list_of_bytes[-2:])
			receive_sum_control = int(receive_sum_control_hex, 16)

			if checksum == receive_sum_control:
				print "Checksum for configuration package verified"
			else:
				print "Wrong checksum, package is not interpreted \n"
				request.finish()
				return 0

			my_smart_id_hex = ''.join('{:02x}'.format(x) for x in list_of_bytes[:2])
			my_smart_id = int(my_smart_id_hex, 16)
			db_operation = DatabaseCommunication()
			query_get_user = "select user_id from device where id = %s" % my_smart_id
			user_id = db_operation.select_operation(query_get_user)[0][0]
			query_get_all_device = "select id from device where user_id = %s" %user_id
			all_device_on_net = db_operation.select_operation(query_get_all_device)
			for device in all_device_on_net:
				device_id_hex = bytearray(pack('H', device[0]))
				device_id_dec_low = int(chr(device_id_hex[1]).encode('hex'), 16)
				device_id_dec_high = int(chr(device_id_hex[0]).encode('hex'), 16)
				list_of_bytes_send.extend([device_id_dec_low, device_id_dec_high])
			package_r = ':'.join(str(x) for x in list_of_bytes_send)
			package_r += ':p'
			print "%r" % package_r

			request.write(package_r)


class SmartboxPage(Resource):
	def render_POST(self, request):
		"""This function is used to get data from esp
           and call function which handling this"""
		data = json.loads(request.content.read())
		print "%r" % data
		d = deferLater(reactor, 0.01, lambda: request)
		d.addCallback(self.handling_samrtbox_data, data)

		return NOT_DONE_YET

		# self.handling_samrtbox_data(request, data)

	def render_GET(self, request):
		""" Simple function to test GET method from esp"""
		print "%r" % request.content.read()
		request.write("cccccccccccccccc")

	# @profile
	def handling_samrtbox_data(self, request, data):
		""" Function that interprets received data from esp
            This function read package of ints that represent
            some functionality, calculate checksum and compare it
            with received checksum. When its not the same function
            closed connection and return 0. Otherwise interprets
            f_key (functionality key) and doing its jobs"""
		list_of_bytes = data['data']
		print "%r" % data['data']
		f_key = list_of_bytes[2]
		list_of_bytes_send = []
		# get id of currently communicating smartbox
		# my_smart_id_hex = ''.join('{:02x}'.format(x) for x in list_of_bytes[:2])
		# my_smart_id = int(my_smart_id_hex, 16)
		# print f_key
		# TODO this will work only if one bit will be set in f_key byte
		# first we must check sum control
		# sum_of_bytes_to_calc_sum_control = sum(list_of_bytes[:-2])

		checksum = CRCCCITT().calculate("".join(map(chr, list_of_bytes[:-2])))
		receive_sum_control_hex = ''.join('{:02x}'.format(x) for x in list_of_bytes[-2:])
		receive_sum_control = int(receive_sum_control_hex, 16)
		db_operation = DatabaseCommunication()
		if checksum == receive_sum_control:
			print "Checksum verified"

		else:
			print "Wrong checksum, package is not interpreted \n"
			request.finish()
			return 0

		list_of_all_smartboxes_id = []
		query_string = ''

		# #################################
		# # Bartek dodaje 1 do danych
		# list_of_bytes[4] -= 1
		# list_of_bytes[5] -= 1
		# #################################

		# this will be done if smartbox work in normal mode (f_key == 1)
		if f_key == f_key_output_state:
			# count smartboxes which are included in package (-2 because last two bytes are bytes of sum controll)
			count_smartboxes = (len(list_of_bytes) - 2) / 5
			print "Stan wyjścia obecny"

			for smartbox in xrange(int(count_smartboxes)):
				# convert bytes to hex, first of two bytes are id of smartbox, so first we need to convert
				# its to hex and next this two bytes convert to one decimal value
				smart_id_hex = ''.join(chr(bt) for bt in list_of_bytes[smartbox * 5:smartbox * 5 + 2])
				# convert id to decimal
				smart_id = int(smart_id_hex.encode('hex'), 16)
				# append all ids to list
				list_of_all_smartboxes_id.append(smart_id)
				# 5 and 6 bytes represent power consumption of electric socket which master smartbox is connected to
				power_consumption_hex = ''.join(chr(bt) for bt in list_of_bytes[smartbox * 5 + 4:smartbox * 5 + 6])
				# convert power consumption to decimal
				power_consumption = int(power_consumption_hex.encode('hex'), 16)
				print "My smart id: %d" % smart_id
				print "Power consumption: %d mA/s" % power_consumption

				# insert to table all records which we get from package
				query = "INSERT INTO device_measurement(deviceid, powerconsumption) VALUES(%d, %d);" % (
					smart_id, power_consumption)
				query_string += query

			db_operation.insert_operation(query_string)
			# db_operation.conn.commit() #this is much faster than doing commit in for loop
			# build package which will be sending
			# TODO what will be send in normal mode?
			# query to check all smartboxes "ison" status
			if len(list_of_all_smartboxes_id) > 1:
				query_ison = "select id, ison, should_reset from device where id in %s" % (
					tuple(list_of_all_smartboxes_id),)
			elif len(list_of_all_smartboxes_id) == 1:
				query_ison = "select id, ison, should_reset from device where id = %s" % list_of_all_smartboxes_id[0]

			result_ison = db_operation.select_operation(query_ison)
			f_key_send = 0;
			list_ids_change_reset = []

			for num, ids in enumerate(list_of_all_smartboxes_id):
				# we must cut decimal id to bytes - 451 -> to hex -> to bytes in dec
				smart_id_hex = bytearray(pack('H', ids))
				smart_id_dec_low = int(chr(smart_id_hex[1]).encode('hex'), 16)
				smart_id_dec_high = int(chr(smart_id_hex[0]).encode('hex'), 16)
				f_key_send += int(result_ison[num][1])
				# if smartob should reset add 4 to f_key (third byte is high)
				if result_ison[num][2]:
					f_key_send += 4
					list_ids_change_reset.append(ids)
				# fill package - id low, id high, ison, pin
				list_of_bytes_send.extend([smart_id_dec_low, smart_id_dec_high, f_key_send])

			# with one element tuple is like (451,) so with this comma it isn't correct query
			if len(list_ids_change_reset) > 1:
				query_change_reset_status = "Update device set should_reset = 'False' where id in %s" % (
					tuple(list_ids_change_reset),)
				db_operation.insert_operation(query_change_reset_status)

			if len(list_ids_change_reset) == 1:
				query_change_reset_status = "Update device set should_reset = 'False' where id = %s" % \
				                            list_ids_change_reset[0]
				db_operation.insert_operation(query_change_reset_status)

			# calculatesum control
			sum_of_bytes = sum(list_of_bytes_send)
			sum_control = CRCCCITT().calculate(str(sum_of_bytes))
			sum_control_array = bytearray(pack('H', sum_control))
			list_of_bytes_send.extend([sum_control_array[1], sum_control_array[0]])

			# print "%r" % list_of_bytes_send
			# print "%r" % ''.join(str(bytearray(list_of_bytes_send)))
			package_r = ':'.join(str(x) for x in list_of_bytes_send)
			package_r += ':p'
			print "%r" % package_r

			request.write(package_r)
			request.finish()

		# Is this really necessary?
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
			port_byte = bytearray(pack('H', port))
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
		# self.conn = adbapi.ConnectionPool("psycopg2", database="smartbox_database", user="postgres", password="postgres", host="127.0.0.1",
		#                              port="5432")
		self.conn = psycopg2.connect(database="smartbox_database", user="postgres", password="postgres",
		                             host="127.0.0.1",
		                             port="5432")

	# @profile
	def select_operation(self, query):
		# database connection
		cur = self.conn.cursor()
		cur.execute(query)
		rows = cur.fetchall()
		# self.conn.close()
		return rows

	# @profile
	def insert_operation(self, query):
		# database connection
		cur = self.conn.cursor()
		cur.execute(query)

		self.conn.commit()

	# return 0
	# self.conn.close()


root = Resource()
root.putChild("api", ApiPage())
root.putChild("smartbox", SmartboxPage())
root.putChild("configuration", SmartboxConfiguration())
factory = Site(root)
application = service.Application("smartbox")
endpoint = endpoints.TCP4ServerEndpoint(reactor, 8880)
endpoint.listen(factory)
reactor.run()
