import yaml
import re
from os import getenv

from .config_models import Config

var_substition_regex = re.compile(r"{{(.*?)}}")

def var_substition(content: str) -> str:
  for match in var_substition_regex.finditer(content):
    # replace {{DNS_UPDATER_VAR_x}} with $x
    if match.group(1).startswith("DNS_UPDATER_VAR_"):
      content = content.replace(match.group(0), getenv(match.group(1)) or "", 1)
  return content


def load_config(config_location: str) -> Config:
  config_file = open(config_location, "r")
  config_str: str = config_file.read()
  config_file.close()

  config_str = var_substition(config_str)

  config_json = yaml.safe_load(config_str)

  # TODO: wrap in try-except and provide better error explanation

  config: Config = Config.model_validate(config_json)

  return config