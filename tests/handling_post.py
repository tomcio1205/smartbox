# -*- coding: utf-8 -*-

import json
import psycopg2
from socket import inet_aton
from struct import pack

from PyCRC.CRCCCITT import CRCCCITT
from twisted.internet import reactor, endpoints, defer, threads
from twisted.web.resource import Resource
from twisted.web.server import Site

from twisted.application import service

from twisted.enterprise import adbapi
from time import sleep

dbpool = adbapi.ConnectionPool("psycopg2", host='127.0.0.1', port=5432, database='smartbox_database',
                            user='postgres', password='postgres', cp_min=3, cp_max=10, cp_noisy=True,
                            cp_reconnect=True, cp_good_sql="SELECT 1")

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
		data = json.loads(request.content.read())
		comma = 0
		# query = "UPDATE device SET ison = '%s' WHERE id = %s" % (data['ison'], data['smart_id'])
		query = "UPDATE device SET "
		if 'ison' in data:
			query += "ison = '%s' " % data['ison']
			comma += 1
		if 'should_reset' in data:
			if comma:
				query += ", "
			query += "should_reset = '%s' " % data['should_reset']
		query += "WHERE id = %s" % data['smart_id']
		db = DatabaseCommunication()
		db.call_cur_query(query)
		# print x['smart_id']
		request.write('<html><body>You submitted: %r</body></html>' % data)  # (cgi.escape(request.content.read()),)

	# request.finish()


class SmartboxPage(Resource):
	def render_POST(self, request):
		data = request.content.read()
		self.handling_samrtbox_data(request, data)

	def render_GET(self, request):
		print "%r" % request.content.read()
		request.write("cccccccccccccccc")

	# @profile
	# @defer.inlineCallbacks
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
		#
		checksum = CRCCCITT().calculate(data[:-2])
		receive_sum_control_hex = ''.join('{:02x}'.format(x) for x in list_of_bytes[-2:])
		receive_sum_control = int(receive_sum_control_hex, 16)
		db_operation = DatabaseCommunication()
		if checksum == receive_sum_control:
			print "Suma kontrolna zweryfikowana poprawnie"
		else:
			print "Sumy kontrolne różne, nie rozpatruję paczki \n"
			#TODO - take steps if checksum are different
			# return 0
		list_of_all_smartboxes_id = []
		smart_pins = {}
		query_string = ''

		# this will be done if smartbox work in normal mode
		if f_key == f_key_output_state:
			# count smartboxes which are included in package (-2 because last two bytes are bytes of sum controll)
			count_smartboxes = (len(list_of_bytes) - 2) / 7
			print "Stan wyjścia obecny"
			for smartbox in xrange(int(count_smartboxes)):
				# convert bytes to hex, first of two bytes are id of smartbox, so first we need to convert
				# its to hex and next this two bytes convert to one decimal value
				smart_id_hex = ''.join(chr(bt) for bt in list_of_bytes[smartbox * 7:smartbox * 7 + 2])
				# convert id to decimal
				smart_id = int(smart_id_hex.encode('hex'), 16)
				# append all ids to list
				list_of_all_smartboxes_id.append(smart_id)
				# 5 and 6 bytes represent power consumption of electric socket which master smartbox is connected to
				power_consumption_hex = ''.join(chr(bt) for bt in list_of_bytes[smartbox * 7 + 4:smartbox * 7 + 6])
				# convert power consumption to decimal
				power_consumption = int(power_consumption_hex.encode('hex'), 16)
				# 7 bytes represent voltage of electric socket which master smartbox is connected to
				current_voltage = list_of_bytes[smartbox * 7 + 6]
				# +3 because pin is fourth in package (we count from 0 so is +3)
				smart_pins[smart_id] = int(chr(list_of_bytes[smartbox * 7 + 3]).encode('hex'), 16)
				print "My smart id: %d" % smart_id
				print "Power consumption: %d mA/s" % power_consumption
				print "Voltage of electrical socket: %d V" % current_voltage
				# insert to table all records which we get from package
				query = "INSERT INTO device_measurement(deviceid, powerconsumption, socketvoltage) VALUES(%d, %d, %d);" % (smart_id, power_consumption, current_voltage)
				query_string = query_string + query
			# yield pool.runInteraction(db_operation.insert_operation, query_string)
			db_operation.insert_operation(query_string)
			# db_operation.conn.commit() #this is much faster than doing commit in for loop
			# build package which will be sending
			# TODO what will be send in normal mode?
			#query to check all smartboxes "ison" status
			query_ison = "select id, ison, should_reset from device where id in %s" % (tuple(list_of_all_smartboxes_id),)
			# result_ison = yield pool.runQuery(query_ison)

			f_key_send = 0
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
				list_of_bytes_send.extend([smart_id_dec_low, smart_id_dec_high, f_key_send, smart_pins[ids]])
			# with one element tuple is like (451,) so with this comma it isn't correct query
			if len(list_ids_change_reset) > 1:
				query_change_reset_status = "Update device set should_reset = 'False' where id in %s" % (tuple(list_ids_change_reset),)
				db_operation.call_cur_query(query_change_reset_status)
			if len(list_ids_change_reset) == 1:
				query_change_reset_status = "Update device set should_reset = 'False' where id = %s" % list_ids_change_reset[0]
				db_operation.call_cur_query(query_change_reset_status)
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
			# d = defer.Deferred()
			d = threads.deferToThread(self.make_delay, request)
			d.addCallback(self.send_response)
			# request.write(package_r)

		#Is this really necessary?
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

	def make_delay(self, request):
		print 'Sleeping'
		sleep(5)
		return request

	def send_response(self, request):
		request.write('1:195:0:144:1:196:1:255:1:197:1:255:126:125:p')
		request.finish()
		# pass
	def get_result(self, result):
		return result


class DatabaseCommunication:

	def select_operation(self, query):
		# cursor.execute(query)
		dbpool.runQuery(query)

	def insert_operation(self, query):
		# cursor.execute(query)
		dbpool.runQuery(query)


root = Resource()
root.putChild("api", ApiPage())
root.putChild("smartbox", SmartboxPage())
factory = Site(root)
application = service.Application("smartbox")
endpoint = endpoints.TCP4ServerEndpoint(reactor, 8880)
endpoint.listen(factory)
reactor.run()
