from forge.entities.base import Base


class Org(Base):
  """Forged Oraganization object.
  Matches nailgun.entity.Organization

  :param Base: forge.entities.Base
  :type Base: BaseClass
  :return: List of Organization entities
  :rtype: list
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
