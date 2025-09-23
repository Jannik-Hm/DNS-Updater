import yaml

from .config_models import Config

def load_config(config_location: str) -> Config:
  config_file = open(config_location, "r")
  config_json = yaml.safe_load(config_file)
  config_file.close()

  # TODO: add env substitution in yaml config (regex matching)

  # TODO: wrap in try-except and provide better error explanation

  config: Config = Config.model_validate(config_json)

  return config