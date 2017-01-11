import psycopg2


class Bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class DatabaseConnection:
    def __init__(self):
        self.conn = psycopg2.connect(database="smartbox_database_uuid", user="postgres", password="postgres",
                                     host="127.0.0.1",
                                     port="5432")

    def select_operation(self, query):
        cur = self.conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        return rows

    def update_operation(self, query):
        cur = self.conn.cursor()
        cur.execute(query)
        self.conn.commit()


class ChechSDK():
    def check_actual_sdk(self):
        db = DatabaseConnection()
        query_last_sdk = "SELECT id FROM sdk_history order by sdk_timestamp desc limit 1"
        last_sdk_version = db.select_operation(query_last_sdk)[0][0]
        query_all_ids = "Update device set is_sdk_actual = True where sdk_version = %d" % last_sdk_version
        db.update_operation(query_all_ids)


if __name__ == '__main__':
    print Bcolors.OKGREEN + "Check SDK Start" + Bcolors.ENDC
    sdk = ChechSDK()
    sdk.check_actual_sdk()
    print Bcolors.OKGREEN + "Done" + Bcolors.ENDC
