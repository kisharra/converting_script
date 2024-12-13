import os
from db_query.db_query import Db_query
import json



def load_config():
    with open (os.path.join('/opt/conversion/settings', 'config.json'), 'r') as config_file:
        config = json.load(config_file)
        return config

create_tables_db = Db_query(load_config())
create_tables_db.create_table()