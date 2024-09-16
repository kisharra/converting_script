import os
from conversion.db_querry import Db_querry
import json



def load_config():
    with open (os.path.join('/opt/conversion/settings', 'config.json'), 'r') as config_file:
        config = json.load(config_file)
        return config

create_tables_db = Db_querry(load_config())
create_tables_db.create_table()