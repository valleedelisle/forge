from forge.entities.base import Base


class Org(Base):
  """ Methot that gets an organisation based on a name
  Uses the default org if no name is provided
  :returns: nailgun.entities.Organization like object
  """
  def __init__(self, cfg, name=None):
    self.entity = "Organization"
    if not name:
      if cfg.satellite["default_org"]:
        self.name = cfg.satellite["default_org"]
      else:
        return
    self.name = name
    super().__init__(cfg, name=name)
    self.item = self.get_or_new(name)
