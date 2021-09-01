import sqlite3

class CmmDatalog():
    
    def __init__(self,db):
        self.db = db
        self.meas_id = 10   
    
    def logMeasurement(self, op_name):
        self.meas_id = self.db.insert_measurement(op_name)
        return  self.meas_id    

    def logProbe(self,x, y, z, meas_id = None):
        if meas_id:
            m_id = meas_id
        elif self.meas_id:
            m_id = self.meas_id
        else:
            raise Exception("Measurement id is not set")

        self.db.insert_probed_value(m_id,x,y,z)

    def logEdge(self, pt0, pt1, z, meas_id = None):
        if meas_id:
            m_id = meas_id
        elif self.meas_id:
            m_id = self.meas_id
        else:
            raise Exception("Measurement id is not set")
        self.db.insert_probed_value(m_id,pt0[0],pt0[1],z)
        self.db.insert_probed_value(m_id,pt1[0],pt1[1],z)
        self.db.insert_edge_value(m_id,pt0,pt1)


class CmmDb():
    def __init__(self, _db_name = "cmm.db"):
        self.db_name = _db_name 
        self.change_status = True     
        self.last_meas_id = 10
        self.last_op_name = ""

    def open(self):
        self.conn = self.create_connection(self.db_name)
        self.cursor = self.conn.cursor()
    
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
        self.cursor.execute("INSERT INTO PROBED_POINTS (measurement_id,x,y,z) VALUES (?,?,?,?)",row_tuple)
        self.conn.commit()
        self.change_status = True
    
    def insert_edge_value(self, meas_id, pt0, pt1):
        row_tuple = (meas_id,pt0[0],pt0[1],pt1[0],pt1[1])
        print("Inserting edge", row_tuple)
        self.cursor.execute("INSERT INTO EDGE_POINTS (measurement_id,x0,y0,x1,y1) VALUES (?,?,?,?,?)",row_tuple)
        self.conn.commit()
        print("Changin status")
        self.change_status = True    
    
    def get_probed_values(self, meas_id):
        self.cursor.execute("select x, y, z from PROBED_POINTS where measurement_id=?",(meas_id,))
        rows = self.cursor.fetchall()
        # for row in rows:
        #     print(row)
        return rows

    def get_edge_values(self, meas_id):
        self.cursor.execute("select x0, y0, x1, y1 from EDGE_POINTS where measurement_id=?",(meas_id,))
        rows = self.cursor.fetchall()
        # for row in rows:
        #     print(row)
        return rows    

    def insert_measurement(self, op_name):
        self.cursor.execute("INSERT INTO MEASUREMENT (op_name, time_stamp) VALUES (?,datetime('now','localtime'))",(op_name,))
        self.conn.commit()
        self.change_status = True
        self.last_meas_id = self.cursor.lastrowid
        self.last_op_name = op_name
        return self.cursor.lastrowid


    def get_last_meas_id(self):
        self.cursor.execute("select max(id) from MEASUREMENT")
        
        last_id = self.cursor.fetchone()
        #print("Last id", last_id[0])
        return int(last_id[0])

    def get_op_name(self, meas_id):
        self.cursor.execute("select op_name from MEASUREMENT where id=?",(meas_id,))
        op_name = self.cursor.fetchone()
        return str(op_name)
def main():
    db = CmmDb()
    db.open()
    #db.insert_measurement("Last test")
    ret = db.get_edge_values(10)
    #n = db.get_op_name(3)
    print(ret)
    db.close()


if __name__ == "__main__":
    main()
    