import yaml

def load_config(config_path):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

def get_blob_container_details(config):
    return config.get('blob_containers', {})

def get_comtrade_settings(config):
    return config.get('comtrade_settings', {})