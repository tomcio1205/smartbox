package = '\x01\xc3\x01\xff\x04\xe2\xe6\x01\xc4\x01\xff\x04\xe2\xe6\x01\xc5\x01\xff\x04\xe2\xe6\xff\xff'

count_smartboxes = (len(package)-2)/7

for smartbox in range(count_smartboxes):

	smart_id_hex = package[smartbox*7:smartbox*7+2]
	# convert id to decimal
	smart_id = int(smart_id_hex.encode('hex'), 16)

	power_consumption_hex = package[smartbox*7+4:smartbox*7+6]
	power_consumption = int(power_consumption_hex.encode('hex'), 16)

	current_voltage_hex = package[6]
	current_voltage = int(current_voltage_hex.encode('hex'), 16)

	print "My smart id: %d" % smart_id
	print "Power consumption: %d mA/s" % power_consumption
	print "Voltage of electrical socket: %d V" % current_voltage

