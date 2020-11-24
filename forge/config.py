import configparser
import importlib.util
import os
from sys import exit

from logzero import logger as log
from nailgun.config import ServerConfig
from dotenv import load_dotenv


class EnvInterpolation(configparser.BasicInterpolation):
  """Interpolation which expands environment variables in values."""

  def before_get(self, parser, section, option, value, defaults):
    value = super().before_get(parser, section, option, value, defaults)
    return os.path.expandvars(value)


class Config(object):
  def __init__(self, config_file):
    self.satellite = None
    self.config_file = config_file
    self.config = configparser.SafeConfigParser(interpolation=EnvInterpolation())
    self.server_config = None
    load_dotenv()

  def read_config(self, satellite_server=None):
    self.config.read(self.config_file)
    if not satellite_server:
      satellite_list = []
      for s in self.config.sections():
        if s.startswith("servers"):
          if self.config[s].getboolean('default'):
            self.satellite = self.config[s]
          satellite_list.append(self.config[s].get('name'))
      if not self.satellite:
        log.error("No default satellite defined. You need to specify one with"
                  "--satellite-server/-s")
        log.info("List of servers in configuration: %s"
                 % ", ".join(satellite_list))
        exit(1)
    else:
      try:
        self.satellite = self.config[f"servers-{satellite_server}"]
      except KeyError:
        log.error(f"Unknown satellite servers: {satellite_server}")
        exit(1)
    self.server_config = ServerConfig(
      verify=False,
      auth=(self.satellite["username"], self.satellite["password"]),
      url="https://%s" % self.satellite["host"]
    )


def load_module(folder, target, class_name=None):
  """ Function to load modules from a file as a class_name.
  This is used by the forger.py command and also used in the entitles.base
  when passing strings as classes to be loaded. """
  if not class_name:
    class_name = target.capitalize()
  if "/" not in folder:
    folder = f"./forge/actions/{folder}"
  file_name = f"{folder}/{target}.py"
  spec = importlib.util.spec_from_file_location(f"{class_name}", file_name)
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  log.debug(f"Loading class {class_name} from {folder} as {module}")
  return getattr(module, class_name)
