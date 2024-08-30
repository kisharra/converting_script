from conversion.db_querry import Db_querry
import json



def load_config(config_file):
    with open ('settings/config.json', 'r') as config_file:  #read config file
        config = json.load(config_file)
    return config

querry = Db_querry(load_config('config.json'))

querry.create_table()
