#!/usr/bin/env python
# -*- coding: utf-8 -*-

from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
import psycopg2
from socket import inet_aton
from struct import pack
import crc16

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

class Echo(Protocol):

    def __init__(self):
        self.lines = []

    def dataReceived(self, data):
        """
        As soon as any data is received, write it back.
        """
        self.lines.append(data)
        # print line
        self.f_key_interpretation(data)
        if not data:
            self.sendResponse()

    def sendResponse(self, send_package):
        # self.sendLine("HTTP/1.1 200 OK")
        # self.sendLine("")
        # responseBody = "Return package : %r\r\n" % send_package
        self.transport.write(send_package)

    # self.transport.loseConnection()

    def f_key_interpretation(self, data):
        # unfortunately python replace escape character \x with \\x so below code convert received string
        # data_replace_backslash = data.replace("\\x", "")
        list_of_bytes = [ord(my_byte) for my_byte in data]
        print "%r" %data
        # Convert the hex string to string of bytes.
        # try:
        # 	data_string_of_bytes = unhexlify(data_replace_backslash)
        # except TypeError:
        # 	print "Błędny format danych"
        # 	return
        #
        # list_of_bytes = bytearray(data_string_of_bytes)
        # print "%r" %list_of_bytes
        f_key = list_of_bytes[2]
        list_of_bytes_send = []
        # get id of currently communicating smartbox
        my_smart_id_hex = ''.join('{:02x}'.format(x) for x in list_of_bytes[:2])
        my_smart_id = int(my_smart_id_hex, 16)
        # print f_key
        # TODO this will work only if one bit will be set in f_key byte

        # first we must check sum control
        calculate_sum_control = sum(list_of_bytes[:-2])
        receive_sum_control_hex = ''.join('{:02x}'.format(x) for x in list_of_bytes[-2:])
        receive_sum_control = int(receive_sum_control_hex, 16)
        print 'wyliczona suma kontrolna: %d' % calculate_sum_control
        print 'otrzymana suma kontrolna %d' % receive_sum_control

        # if calculate_sum_control != receive_sum_control:
        # 	print "Błędna suma kontrolna"
        # 	return

        if f_key == f_key_empty_memory:
            print "Mam pustą pamięć proszę o paczkę konfiguracji"

            # TODO this query is hardcoded,it must be changed
            query = "Select ip_adress, port from servers where id = 1"
            query_result = self.database_operation(query, "select")
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

        if f_key == f_key_ready_for_configuration:
            # \x01\xc3\x40\xff\x04\xe2

            print "Dobra jestem gotowy na przyjęcie nowej paczki z konfiguracją - dawaj ją!"

            # TODO this query is hardcoded,it must be changed
            query = "Select ip_adress, port from servers where id = 1"
            query_result = self.database_operation(query, "select")
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
            network_id = self.database_operation(query_network_id, "select")[0][0]
            query = "Select smart_id, smart_password from smartbox_settings where network_id = %d" % network_id
            all_smartboxes_ids = self.database_operation(query, "select")
            smartboxes_count = len(all_smartboxes_ids)
            # -1 beacuse select return also id of master smartbox
            # 128 because its means that this package is the configuration package
            list_of_bytes_send.extend([list_of_bytes[0], list_of_bytes[1], 128, list_of_bytes[3], ip_byte[0],
                                       ip_byte[1], ip_byte[2], ip_byte[3], port_byte[0], port_byte[1],
                                       smartboxes_count - 1])

            if all_smartboxes_ids:
                for ids in all_smartboxes_ids:
                    # send ids of smartboxes which id is different than currently comunicating smartbox
                    if ids[0] != my_smart_id:
                        next_smart_id = bytearray(pack('h', ids[0]))
                        # in this order because first is send high byte
                        list_of_bytes_send.extend([next_smart_id[1], next_smart_id[0], int(ids[1])])
            # TODO send sum control
            # generate sum control  by crc16 module
            sum_of_bytes = sum(list_of_bytes_send)
            sum_control = crc16.crc16xmodem(str(sum_of_bytes))
            sum_control_array = bytearray(pack('h', sum_control))
            list_of_bytes_send.extend([sum_control_array[1], sum_control_array[0]])
            print "%r" % list_of_bytes_send

            # list_of_bytes_send_hex = [hex(x) for x in list_of_bytes_send]
            self.sendResponse(bytes(list_of_bytes_send))

        if f_key == f_key_report:
            # \x01\xc3\x10\xff\x04\xe2\xe6\x01\xc4\x01\xff\x04\xe2\xe6\x01\xc5\x01\xff\x04\xe2\xe6\xff\xff
            print "Ta paczka to raport na temat sieci i ostatniego połaczenia"


        if f_key == f_key_wrong_pin:
            print "W naszej poprzedniej rozmowie podałeś błędny PIN"
        if f_key == f_key_draw_current:
            print "Coś pobiera prąd w mniejszym lub większym stopniu prąd ale jednak"
        if f_key == f_key_alarm:
            print "Zaistniał alarm z przeciążenia/zwarcie gniazdka"
        if f_key == f_key_output_state:

            # \x01\xc3\x01\xff\x04\xe2\xe6\x01\xc4\x01\xff\x04\xe2\xe6\x01\xc5\x01\xff\x04\xe2\xe6\xff\xff

            count_smartboxes = (len(list_of_bytes)-2)/7
            print "Stan wyjścia obecny"

            for smartbox in range(count_smartboxes):
                smart_id_hex = ''.join(chr(bt) for bt in list_of_bytes[smartbox*7:smartbox*7+2])
                # convert id to decimal
                smart_id = int(smart_id_hex.encode('hex'), 16)

                # 5 and 6 bytes represent power consumption of electric socket which master smartbox is connected to
                power_consumption_hex = ''.join(chr(bt) for bt in list_of_bytes[smartbox*7+4:smartbox*7+6])
                # convert power consumption to decimal
                power_consumption = int(power_consumption_hex.encode('hex'), 16)

                # 7 bytes represent voltage of electric socket which master smartbox is connected to
                # current_voltage_hex = chr(list_of_bytes[smartbox*7+6])
                # convert voltage to decimal
                # current_voltage = int(current_voltage_hex.encode('hex'), 16)
                current_voltage = list_of_bytes[smartbox*7+6]

                print "My smart id: %d" % smart_id
                print "Power consumption: %d mA/s" % power_consumption
                print "Voltage of electrical socket: %d V" % current_voltage



            # build package which will be sending
            list_of_bytes_send.extend([list_of_bytes[0], list_of_bytes[1], 128, list_of_bytes[3]])
            self.sendResponse(bytes(list_of_bytes_send))

    def database_operation(self, query, query_type):
        # database connection
        conn = psycopg2.connect(database="smartbox", user="postgres", password="postgres", host="127.0.0.1",
                                port="5432")
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        return rows
        conn.close()


def main():
    f = Factory()
    f.protocol = Echo
    reactor.listenTCP(8080, f)
    reactor.run()

if __name__ == '__main__':
    main()
