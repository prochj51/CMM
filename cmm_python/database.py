import sqlite3

class CmmDatalog():
    
    def __init__(self,db):
        self.db = db
        self.meas_id = 10   
    
    def logMeasurement(self, op_name):
        self.db.insert_measurement(op_name)
        self.meas_id = self.db.get_last_meas_id()
        self.db.last_meas_id = self.meas_id
        return self.meas_id    

    def logProbe(self,x, y, z, meas_id_ = None):
        if meas_id_ is not None:
            meas_id = meas_id_
        elif self.meas_id is not None :
            meas_id = self.meas_id
        else:
            raise Exception("Measurement id is not set")

        self.db.insert_probed_value(meas_id,x,y,z)

class CmmDb():
    def __init__(self, _db_name = "cmm.db"):
        self.db_name = _db_name 
        self.change_status = True     
        self.last_meas_id = 10

    def open(self):
        self.conn = self.create_connection(self.db_name)
        self.c = self.conn.cursor()
    
    def create_connection(self,db_file):
        """ create a database connection to the SQLite database
            specified by the db_file
        :param db_file: database file
        :return: Connection object or None
        """
        conn = None
        try:
            conn = sqlite3.connect(db_file)
        except Error as e:
            print(e)
        print("Connected succesfully to {}".format(db_file))
        return conn    
    
    def close(self):
        print("Closing db connection")
        self.conn.close()

    def insert_probed_value(self, meas_id, x, y, z):
        row_tuple = (meas_id,x,y,z)
        print("Inserting", row_tuple)
        self.c.execute("INSERT INTO PROBED_POINTS (measurement_id,x,y,z) VALUES (?,?,?,?)",row_tuple)
        self.conn.commit()
        self.change_status = True
    
    def get_probed_values(self, meas_id):
        self.c.execute("select x, y, z from PROBED_POINTS where measurement_id=?",(meas_id,))
        rows = self.c.fetchall()
        # for row in rows:
        #     print(row)
        return rows

    def insert_measurement(self, op_name):
        self.c.execute("INSERT INTO MEASUREMENT (op_name, time_stamp) VALUES (?,datetime('now','localtime'))",(op_name,))
        self.conn.commit()
        self.change_status = True
    

    def get_last_meas_id(self):
        self.c.execute("select max(id) from MEASUREMENT")
        
        last_id = self.c.fetchone()
        #print("Last id", last_id[0])
        return int(last_id[0])

def main():
    db = CMM_Db()
    db.open()
    
    #r = db.get_probed_values(10)
    db.insert_measurement("perpendicularity")
    print(db.get_last_meas_id()[0])
    db.close()


if __name__ == "__main__":
    main()
    