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

from txrestapi.methods import GET, POST
from txrestapi.resource import APIResource

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


class HttpRest(APIResource):
	@POST('^/smartbox/(?P<word>[^/]*)')
	def smartbox_post(self, request, word):
		data = json.loads(request.content.read())
		print "############# Received normal package #############"
		print "%r \n" % data
		if word == 'work':
			smart = SmartboxPage()
			smart.handling_samrtbox_data(request, data)
		if word == 'configuration':
			conf = SmartboxConfiguration()
			conf.handling_configuration_data(request, data)

	@POST('^/api/device')
	def smartbox_conf_post(self, request):
		data = json.loads(request.content.read())
		db_operation = DatabaseCommunication()
		query = "Update device set name='{ne}', ison={io}, simulatepresence={se} where id={id}".format(ne=data['Name'],
		                                                                                               io=data['IsOn'],
		                                                                                               se=data['SimulatePresence'],
		                                                                                               id=data['ID'])
		db_operation.insert_operation(query)
		return "Table updated"

	@GET('^/api/(?P<word>[^/]*)/(?P<id>[^/]+)')
	def api_post(self, request, word, id):
		db_operation = DatabaseCommunication()
		data = {}
		if word == 'devices':
			query = "SELECT id, room, name, ison, antitheft, simulatepresence, user_id, icon_type FROM device WHERE id = %s" % id
			devices = db_operation.select_operation(query)[0]
			data['ID'] = devices[0]
			data['IsConnectedOn'] = False
			data['Name'] = devices[2]
			data['IsOn'] = devices[3]
			data['AntiTheft'] = devices[4]
			data['SimulatePresence'] = devices[5]
			data['UserId'] = devices[6]
			data['Room'] = devices[1]
			data['IconType'] = devices[7]
			json_data = json.dumps([data])
			return json_data
		if word == 'user':
			data_list = []
			query = "SELECT id, room, name, ison, antitheft, simulatepresence, user_id, icon_type FROM device WHERE user_id = %s" % id
			devices = db_operation.select_operation(query)
			for device in devices:
				data = {
					'ID': device[0],
					'IsConnectedOn': False,
					'Name': device[2],
					'IsOn': device[3],
					'AntiTheft': device[4],
					'SimulatePresence': device[5],
					'UserId': device[6],
					'Room': device[1],
					'IconType': device[7],
				}
				data_list.append(data)
			json_data = json.dumps(data_list)
			return json_data
		else:
			return "Wrong URL"


class ApiPage(Resource):
	def render_device_id(self, request, id):
		""" Function to handling GET method from api """
		db_operation = DatabaseCommunication()
		data = {}
		query = "SELECT id, isdeleted, name, ison, antitheft, simulatepresence, user_id FROM device WHERE id = %s" % id
		devices = db_operation.select_operation(query)[0]
		data['id'] = devices[0]
		data['isdeleted'] = devices[1]
		data['name'] = devices[2]
		data['ison'] = devices[3]
		data['antitheft'] = devices[4]
		data['simulatepresence'] = devices[5]
		data['user_id'] = devices[6]
		json_data = json.dumps(data)
		request.write(json_data)

	def render_device_user(self, request, user_id):
		""" Function to handling GET method from api """
		db_operation = DatabaseCommunication()
		data = {}
		query = "SELECT id, isdeleted, name, ison, antitheft, simulatepresence, user_id FROM device WHERE id = %s" % id
		devices = db_operation.select_operation(query)[0]
		data['id'] = devices[0]
		data['isdeleted'] = devices[1]
		data['name'] = devices[2]
		data['ison'] = devices[3]
		data['antitheft'] = devices[4]
		data['simulatepresence'] = devices[5]
		data['user_id'] = devices[6]
		json_data = json.dumps(data)
		request.write(json_data)


class SmartboxConfiguration(Resource):
	def handling_configuration_data(self, request, data):

		device_id = data['ID']
		device_mode = data['Mode']
		db_operation = DatabaseCommunication()
		query_get_user = "select user_id from device where id = '%s'" % device_id
		user_id = db_operation.select_operation(query_get_user)[0][0]
		data_list = []

		if device_mode == "Work":
			query_get_devices_state = "select id, is_on from device where user_id = %s" % user_id
			devices_state = db_operation.select_operation(query_get_devices_state)
			for state in devices_state:
				j_data = {
					'ID': state[0],
					'IsOn': state[1],
				}
				data_list.append(j_data)

		if device_mode == "Config":
			query_get_all_device = "select id from device where user_id = %s" % user_id
			all_device_on_net = db_operation.select_operation(query_get_all_device)
			for device in all_device_on_net:
				j_data = {
					'ID': device[0],
				}
				data_list.append(j_data)
		else:
			j_data = {
				'Error': "Can't properly read mode %s" % device_mode
			}
			data_list.append(j_data)
		json_data = json.dumps(data_list)

		print "############# sent configuration package #############"
		print "%r\n" % json_data

		request.write(json_data)


class SmartboxPage(Resource):
	# @profile
	def handling_samrtbox_data(self, request, data):
		""" Function that interprets received data from esp
            This function read package of ints that represent
            some functionality, calculate checksum and compare it
            with received checksum. When its not the same function
            closed connection and return 0. Otherwise interprets
            f_key (functionality key) and doing its jobs"""
		list_of_bytes = data['data']
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
			print "Checksum for normal package verified \n"

		else:
			print "Wrong checksum, package is not interpreted \n"
			# request.finish()
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
				print "Power consumption: %d mA/s\n" % power_consumption

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
			print "############# Sent normal package #############"
			print "%r\n" % package_r
			request.write(package_r)
		# request.finish()

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
		self.conn = psycopg2.connect(database="smartbox_database_uuid", user="postgres", password="postgres",
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


api = HttpRest()
# root = Resource()content
# root.putChild("api", ApiPage())
# root.putChild("smartbox", SmartboxPage())
# root.putChild("configuration", SmartboxConfiguration())
factory = Site(api)
# application = service.Application("smartbox")
reactor.listenTCP(8880, factory)
reactor.run()
