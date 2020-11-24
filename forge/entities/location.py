from forge.entities.base import Base


class Location(Base):
  """ Methot that gets a location based on a name
  Uses the default location if no name is provided
  :returns: nailgun.entities.Organization like object
  """
  def __init__(self, cfg, name=None):
    self.entity = "Location"
    if not name:
      if self._cfg.satellite["default_location"]:
        self.name = self._cfg.satellite["default_location"]
      else:
        return
    self.name = name
    super().__init__(cfg, name=name)
    self.item = self.get_or_new(name)
