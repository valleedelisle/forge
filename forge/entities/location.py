from forge.entities.base import Base


class Location(Base):
  """Forged Location object.
  Matches nailgun.entity.Location

  :param Base: forge.entities.Base
  :type Base: BaseClass
  :return: List of Location entities
  :rtype: list
  """
  def __init__(self, cfg, name=None):
    """Class initialization

    :param cfg: Configuration object
    :type cfg: forge.config
    """
    self.entity = "Location"
    if not name:
      if self._cfg.satellite["default_location"]:
        self.name = self._cfg.satellite["default_location"]
      else:
        return
    self.name = name
    super().__init__(cfg, name=name)
    self.item = self.get_or_new(name)
