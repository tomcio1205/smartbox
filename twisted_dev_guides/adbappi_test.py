from twisted.enterprise import adbapi
from twisted.internet import reactor, defer

dbpool = adbapi.ConnectionPool("psycopg2", host='127.0.0.1', port=5432, database='smartbox_database',
                            user='postgres', password='postgres', cp_min=3, cp_max=10, cp_noisy=True,
                            cp_reconnect=True, cp_good_sql="SELECT 1")

class ddd:
    def getName(self,email):
        return dbpool.runQuery("SELECT name FROM device WHERE id = %d" % email)

    def printResults(self,results):
        self.d = defer.Deferred()
        for elt in results:
            self.d.addCallback(self.print_result)
            print elt[0]
        return self.d

    def finish(self):
        dbpool.close()
        reactor.stop()

    def print_result(self):
        return "ssss"

    def ebPrintError(failure):
        import sys
        sys.stderr.write(str(failure))

c = ddd()
d = c.getName(451)
d.addCallback(c.printResults)
d.addCallback(c.print_result)
d.addErrback(c.ebPrintError)

reactor.callLater(1, c.finish)
reactor.run()

