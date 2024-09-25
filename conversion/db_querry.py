import os
import sqlite3
import mariadb
import logging
import json

class Db_querry():
    def __init__(self, config):
        """
        Initialize class variables

        Parameters
        ----------
        config : dict
            config dictionary

        Attributes
        ----------
        config : dict
            config dictionary
        db_file : str
            path to database file
        maria_db : dict
            config of maria database
        log_file : str
            path to log file
        """
        self.config = config
        self.db_file = os.path.join(config['path_to_main'], config['sqlite3'])
        self.maria_db = config['maria_db']
        self.log_file = os.path.join(config['path_to_main'], config['log_file'])
        logging.basicConfig(filename=self.log_file, level=logging.ERROR, format='%(asctime)s:%(message)s')

    def table_exists(self, table_name):
        """
        Check if table exists in database

        Parameters
        ----------
        table_name : str
            name of table to check

        Returns
        -------
        bool
            True if table exists, False otherwise
        """
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
        """
        Create tables in database if they do not exist

        This function creates 'Files' and 'ConversionTasks' tables in database if they do not exist.
        """
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
            
    def save_file_data(self, data, streams, is_film, is_serial):
        """
        Save file data to the database.

        Parameters
        ----------
        data : dict
            Data of the file, returned by ffmpeg.
        streams : list of dict
            List of streams of the file.
        is_film : bool
            Flag indicating if the file is a film.
        is_serial : bool
            Flag indicating if the file is a serial.
        """
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM Files WHERE filename = ?', (data['format']['filename'],))
            
            if cur.fetchone() is None:
                try:
                    filename = data['format'].get('filename')
                    nb_streams = data['format'].get('nb_streams')
                    size = data['format'].get('size')
                    bit_rate = data['format'].get('bit_rate')  

                    if filename:
                        cur.execute("""INSERT INTO Files (filename, IsFilm, IsSerial, IsConverted, nb_streams, size, bit_rate, streams)  
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                                        (filename, is_film, is_serial, False, nb_streams, size, bit_rate, json.dumps(streams)))
                        conn.commit()
                    else:
                        logging.error("Filename is missing in the data.")
                
                except sqlite3.Error as e:
                    logging.error(f'Error inserting data: {e}')
            else:
                print(f"Data already exists for {data['format']['filename']}")

    def interrupted_program(self, current_time, file_id):
        """
        Update ConversionTasks table with status 'Error: check logs' and current time if program is interrupted
        
        Parameters
        ----------
        current_time : str
            current date and time in format '%Y-%m-%d %H:%M:%S'
        file_id : int
            id of file in database
        """
        
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute('UPDATE ConversionTasks SET status=?, end_time=? WHERE file_id=?', ('Error: check logs', current_time, file_id))  #update if program interrupted
            conn.commit()

    def select_data(self):
        """
        Select data from database

        Returns
        -------
        list of tuples
            list of files with their id, IsFilm, IsConverted, filename, nb_streams, streams
        """
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute('SELECT id, IsFilm, IsConverted, filename, nb_streams, streams FROM Files')  #select data from database
            return cur.fetchall()
        
    def select_single_data(self, filename):
            with sqlite3.connect(self.db_file) as conn:
                cur = conn.cursor()
                cur.execute('SELECT id, IsFilm, IsConverted, filename, nb_streams, streams FROM Files WHERE filename=?', (filename,))  #select data from database
                return cur.fetchall()
    
    def update_status_of_conversion(self, file_id, status, current_time):
        """
        Update ConversionTasks table with status and current time of start of conversion
        
        Parameters
        ----------
        file_id : int
            id of file in database
        status : str
            status of conversion
        current_time : str
            current date and time in format '%Y-%m-%d %H:%M:%S'
        """
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute('INSERT INTO ConversionTasks (file_id, status, start_time) VALUES (?, ?, ?)', (file_id, status, current_time))  #update status of conversion
            conn.commit()
    
    def update_status_ending_conversion(self, status, current_time, check_result, file_id):
        """
        Update ConversionTasks table with status, current time of end of conversion and result of integrity check
        
        Parameters
        ----------
        status : str
            status of conversion
        current_time : str
            current date and time in format '%Y-%m-%d %H:%M:%S'
        check_result : str
            result of integrity check
        file_id : int
            id of file in database
        """
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute('UPDATE ConversionTasks SET status=?, end_time=?, check_integrity=? WHERE file_id=?', (status, current_time, check_result, file_id))  #update status of conversion
            conn.commit()
    
    def update_files_table(self, output_file, is_conveted, nb_streams, size, bitrate, streams, file_id):
        """
        Update table 'Files' with new data
        
        Parameters
        ----------
        output_file : str
            path to output file
        is_conveted : bool
            flag to check if file is converted
        nb_streams : int
            number of streams in file
        size : int
            size of file in bytes
        bitrate : int
            bitrate of file
        streams : str
            json string of streams of file
        file_id : int
            id of file in database
        """
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute('UPDATE Files SET filename=?, IsConverted=?, nb_streams=?, size=?, bit_rate=?, streams=? WHERE id=?', (output_file, is_conveted, nb_streams, size, bitrate, streams, file_id))  #update table 'Files' with new data  #update status of conversion
            conn.commit()

    def update_of_checking_integrity(self, status, current_time, check_result, file_id):
        """
        Update ConversionTasks table with status, current time of end of checking and result of integrity check
        
        Parameters
        ----------
        status : str
            status of checking
        current_time : str
            current date and time in format '%Y-%m-%d %H:%M:%S'
        check_result : str
            result of integrity check
        file_id : int
            id of file in database
        """
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute('UPDATE ConversionTasks SET status=?, end_time=?, check_integrity=? WHERE file_id=?', (status, current_time, check_result, file_id))  #update status of checking
            conn.commit()

    def update_url_file(self, filename, output_file):
        """
        Update url in video_series_files table in maria database
        
        Parameters
        ----------
        filename : str
            original filename
        output_file : str
            new filename
        """
        with mariadb.connect(
            host = self.config['maria_db']['host'],
            user = self.config['maria_db']['user'],
            password = self.config['maria_db']['password'],
            database = self.config['maria_db']['database'],
            port = self.config['maria_db']['port']
        ) as conn:
            cur = conn.cursor()
            cur.execute(
            'UPDATE video_series_files SET url = REPLACE(url, ?, ?) WHERE url LIKE ?',
            (filename, output_file, '%' + filename)
        )
            conn.commit() 

    def global_interrupted_querry(self, current_time):
        with sqlite3.connect(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute('UPDATE ConversionTasks SET status=?, end_time=? WHERE status="converting"', ('Conversion interrupted', current_time)) 
            return cur.fetchall()

    

if __name__ == '__main__':
    pass