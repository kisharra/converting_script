import sqlite3
import logging
import json

class Db_querry():
    def __init__(self, config):
        self.config = config
        self.db_file = config['db_file']
        self.log_file = config['log_file']
        logging.basicConfig(filename=self.log_file, level=logging.ERROR, format='%(asctime)s:%(message)s')

    def table_exists(self, table_name):
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            if not cur:
                return False
            try:
                cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                return cur.fetchone() is not None
            except sqlite3.Error as e:
                logging.error(f'Error executing query: {e}')
                return False

    def create_table(self):
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            if not cur:
                return
            
            if not self.table_exists('Files'):
                create_table_query1 = """CREATE TABLE IF NOT EXISTS Files(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            filename VARCHAR(255),
                            IsFilm BOOLEAN,
                            IsSerial BOOLEAN,
                            IsConverted BOOLEAN,
                            nb_streams INTEGER,
                            size INTEGER,
                            bit_rate INTEGER,
                            streams VARCHAR(255)
                );"""
                try:
                    cur.execute(create_table_query1)
                    conn.commit()
                    print("Table 'Files' created successfully")
                except sqlite3.Error as e:
                    logging.error(f'Error creating table Files: {e}')
            
            if not self.table_exists('ConversionTasks'):
                create_table_query2 = """CREATE TABLE IF NOT EXISTS ConversionTasks(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            file_id INTEGER REFERENCES Files(id),
                            status VARCHAR(255),
                            start_time DATETIME,
                            end_time DATETIME,
                            check_integrity VARCHAR(255)
                );"""
                try:
                    cur.execute(create_table_query2)
                    conn.commit()
                    print("Table 'ConversionTasks' created successfully")
                except sqlite3.Error as e:
                    logging.error(f'Error creating table ConversionTasks: {e}')
            
    def save_films(self, data, streams):
        '''save film data to database'''
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM Files WHERE filename = ?', (data['format']['filename'],))  #check if data already exists
            count = cur.fetchone()
            if count is None:
                try:
                    #insert data in to database
                    cur.execute("""INSERT INTO Files (filename, IsFilm, IsSerial, IsConverted, nb_streams, size, bit_rate, streams)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                                (data['format']['filename'],True, False, False, data['format']['nb_streams'], 
                                data['format']['size'], data['format']['bit_rate'], json.dumps(streams)))
                    conn.commit()
                except sqlite3.Error as e:
                    logging.error(f'Error inserting data: {e}')
            else:
                print(f"Data already exists for {data['format']['filename']}")

    def save_serials(self, data, streams):
        '''save serials data to database'''
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM Files WHERE filename = ?', (data['format']['filename'],))  #check if data already exists
            count = cur.fetchone()
            if count is None:
                try:
                    #insert data in to database
                    cur.execute("""INSERT INTO Files (filename, IsFilm, IsSerial, IsConverted, nb_streams, size, bit_rate, streams)  
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                                (data['format']['filename'], False, True, False, data['format']['nb_streams'], 
                                data['format']['size'], data['format']['bit_rate'], json.dumps(streams)))
                    conn.commit()
                except sqlite3.Error as e:
                    logging.error(f'Error inserting data: {e}')
            else:
                print(f"Data already exists for {data['format']['filename']}")
    
    def interruted_program(self, current_time, file_id):
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute('UPDATE ConversionTasks SET status=?, end_time=? WHERE file_id=?', ('Error: check logs', current_time, file_id))  #update if program interrupted
            conn.commit()

    def select_data(self):
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute('SELECT id, IsFilm, IsConverted, filename, nb_streams, streams FROM Files')  #select data from database
            return cur.fetchall()
    
    def update_status_of_conversion(self, file_id, status, current_time):
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute('INSERT INTO ConversionTasks (file_id, status, start_time) VALUES (?, ?, ?)', (file_id, status, current_time))  #update status of conversion
            conn.commit()
    
    def update_status_ending_conversion(self, status, current_time, check_result, file_id):
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute('UPDATE ConversionTasks SET status=?, end_time=?, check_integrity=? WHERE file_id=?', (status, current_time, check_result, file_id))  #update status of conversion
            conn.commit()
    
    def update_files_table(self, output_file, is_conveted, nb_streams, size, bitrate, streams, file_id):
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute('UPDATE Files SET filename=?, IsConverted=?, nb_streams=?, size=?, bit_rate=?, streams=? WHERE id=?', (output_file, is_conveted, nb_streams, size, bitrate, streams, file_id))  #update table 'Files' with new data  #update status of conversion
            conn.commit()

    def update_of_checking_integrity(self, status, current_time, check_result, file_id):
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute('UPDATE ConversionTasks SET status=?, end_time=?, check_integrity=? WHERE file_id=?', (status, current_time, check_result, file_id))  #update status of checking
            conn.commit()
    

if __name__ == '__main__':
    pass