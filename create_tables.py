import sqlite3


def create_table(cur):
    if not table_exists(cur, 'storage_info'):
        create_table_querry0 = """CREATE TABLE IF NOT EXISTS Films(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename VARCHAR(255),
                    nb_streams INTEGER,
                    size INTEGER,
                    bit_rate INTEGER,
                    streams VARCHAR(255)
        );
        """
    if not table_exists(cur, 'storage_info'):
        create_table_querry1 = """CREATE TABLE IF NOT EXISTS Serials(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename VARCHAR(255),
                    nb_streams INTEGER,
                    size INTEGER,
                    bit_rate INTEGER,
                    streams VARCHAR(255)
        );
        """
    if not table_exists(cur, 'storage_info'):
        create_table_querry2 = """CREATE TABLE IF NOT EXISTS ConversionTasks(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    films_id INTEGER REFERENCES Films(id),
                    serials_id INTEGER REFERENCES Serials(id),
                    status VARCHAR(255),
                    start_time DATETIME,
                    end_time DATETIME,
                    check_integrity VARCHAR(255),
                    new_filename VARCHAR(255)
                    
        );
        """
        try:
            cur.execute(create_table_querry0)
            cur.execute(create_table_querry1)
            cur.execute(create_table_querry2)
            print("Table created successfully")
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")
    else:
        print("Table already exists")

def table_exists(cur, table_name):
    cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    return cur.fetchone() is not None


def main():
    conn = None
    try:
        with sqlite3.connect('/opt/film_storage.db') as conn:
            cur = conn.cursor() 
            create_table(cur)
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
    finally:
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    main()