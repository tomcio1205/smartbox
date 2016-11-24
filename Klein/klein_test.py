# -*- coding: utf-8 -*-

from klein import Klein
import json
import psycopg2
from PyCRC.CRCCCITT import CRCCCITT


class HttpRest(object):
	app = Klein()

	@app.route('/smartbox/<string:word>', methods=['POST'])
	def smartbox_post(self, request, word):
		data = json.loads(request.content.read())
		print "############# Received normal package #############"
		print "%r \n" % data
		if word == 'work':
			smart = Smartbox()
			smart.handling_smartbox_data(data)
		if word == 'configuration':
			conf = SmartboxConf()
			z = conf.handling_configuration_data(data)
			return str(z)

	@app.route('/api/device', methods=['POST'])
	def smartbox_conf_post(self, request):
		data = json.loads(request.content.read())
		db_operation = DatabaseCommunication()
		query = "Update device set name='{ne}', is_on={io}, simulate_presence={se} where id='{id}'".format(ne=data['Name'],
																									   io=data['IsOn'],
																									   se=data['SimulatePresence'],
																									   id=data['ID'])
		db_operation.insert_operation(query)
		return "Table updated"

	@app.route('/api/devices/<string:device_id>', methods=['GET'])
	def api_post(self, request, device_id):
		db_operation = DatabaseCommunication()
		data = {}
		query = "SELECT id, room, name, is_on, anti_theft, simulate_presence, user_id, icon_type FROM device " \
				"WHERE id = '%s'" % device_id
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

	@app.route('/api/user/<string:user_id>', methods=['GET'])
	def api_post(self, request, user_id):
		db_operation = DatabaseCommunication()
		data_list = []
		query = "SELECT id, room, name, is_on, anti_theft, simulate_presence, user_id, icon_type FROM device " \
				"WHERE user_id = %s" % user_id
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


class Smartbox(object):
	def __init__(self):
		pass

	def handling_smartbox_data(self, data):
		list_key = []
		query_string = ''
		db_operation = DatabaseCommunication()
		for key in data:
			list_key.append(key)
			print "My smart id: %s" % key
			print "Power consumption: %d mA/s\n" % data[key]

			# insert to table all records which we get from package
			query = "INSERT INTO device_measurement(device_id, power_consumption) VALUES('%s', %d);" % (
				key, data[key])
			query_string += query

		db_operation.insert_operation(query_string)


class SmartboxConf(object):
	def __init__(self):
		pass

	def handling_configuration_data(self, data):
		device_id = data['ID']
		device_mode = data['Mode']
		db_operation = DatabaseCommunication()
		query_get_user = "select user_id from device where id = '%s'" % device_id
		user_id = db_operation.select_operation(query_get_user)[0][0]
		jj_data = {}
		if device_mode == "Config":
			query_get_all_device = "select id from device where user_id = %s" % user_id
			all_device_on_net = db_operation.select_operation(query_get_all_device)
			for enum, device in enumerate(all_device_on_net):
				j_data = {
					'ID': device[0],
				}
				jj_data[enum] = j_data
				jj_data['CountDevice'] = enum

		if device_mode == "Work":
			query_get_devices_state = "select id, is_on from device where user_id = %s" % user_id
			devices_state = db_operation.select_operation(query_get_devices_state)
			for enum, state in enumerate(devices_state):
				j_data = {
					'ID': state[0],
					'IsOn': state[1],
				}
				jj_data[enum] = j_data
				jj_data['CountDevice'] = enum
		json_data = json.dumps(jj_data)

		print "############# sent configuration package #############"
		print "%r\n" % json_data

		return json_data


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


store = HttpRest()
store.app.run('0.0.0.0', 8080)