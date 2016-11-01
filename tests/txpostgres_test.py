from twisted.internet import reactor
from twisted.python import log, util
from txpostgres import txpostgres
# connect to the database
conn = txpostgres.Connection()
d = conn.connect(database="smartbox_database", user="postgres", password="postgres", host="127.0.0.1",
                              port="5432")
result = ''
def got(rows):
    global result
    result = rows
    return result

# run the query and print the result
d.addCallback(lambda _: conn.runQuery('select id, ison, should_reset from device where id=451'))
d.addCallback(got)

# close the connection, log any errors and stop the reactor
d.addCallback(lambda _: conn.close())
d.addErrback(log.err)
# d.addBoth(lambda _: reactor.stop())

# start the reactor to kick off connection estabilishing
reactor.run()