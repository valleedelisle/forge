from forge.entities.base import Base


class Domains(Base):
  """Forged Domain object.
  Matches nailgun.entity.Domain

  :param Base: forge.entities.Base
  :type Base: BaseClass
  :return: List of Domain entities
  :rtype: list
  """
  def __init__(self, cfg, orgs=[], name=None):
    """Class initialization

    :param cfg: Configuration object
    :type cfg: forge.config
    :param orgs: forged Org objects
    :type orgs: list, forge.entities.Org
    """
    self.entity = "Domain"
    if name:
      self.name = name
    super().__init__(cfg, orgs=orgs, name=name)

  def create_all(self):
    for section in self._cfg.config:
      if section.startswith("domains"):
        item = self.new_item()
        item.name = "-".join(section.split("-")[1:])
        item.__dict__.update(dict(self._cfg.config.items(section)))
        item.organization = item.orgs
        item.location = item.locations
        delattr(item, "orgs")
        delattr(item, "locations")
        self.create(item, attribute_converter={"organization": "Org",
                                               "location": "Location"})
