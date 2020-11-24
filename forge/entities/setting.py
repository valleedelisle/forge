from logzero import logger as log

from forge.entities.base import Base


class Settings(Base):
  """Forged Setting object.
  Matches nailgun.entity.Setting

  :param Base: forge.entities.Base
  :type Base: BaseClass
  :return: List of Setting entities
  :rtype: list
  """
  def __init__(self, cfg):
    self.entity = "Setting"
    super().__init__(cfg)

  def set(self, setting, value):
    if setting.value != value:
      log.info(f"Updating setting {setting.name} with {value}")
      setting.value = value
      setting.update()

  def set_all(self):
    section = "settings-%s" % self._cfg.satellite['name']
    if section not in self._cfg.config:
      log.warn(f"No setting section for {self._cfg.satellite['name']} in "
                "configuration.")
      return False
    if not self.items:
      self.get_all()
    for name in self._cfg.config[section]:
      setting = self.find(name)
      if not setting:
        log.warn(f"Invalid setting {name}")
        continue
      if setting.settings_type == "integer":
        value = self._cfg.config[section].getint(name)
      else:
        value = self._cfg.config[section].get(name)
      log.info(f"Validating {name} is {value}")
      self.set(setting, value)
