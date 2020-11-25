from forge.entities.base import Base


class RPMContentViewFilters(Base):
  """Forged RPMContentViewFilters object.
  Matches nailgun.entity.RPMContentViewFilters

  :param Base: forge.entities.Base
  :type Base: BaseClass
  :return: List of RPMContentViewFilters entities
  :rtype: list
  """
  def __init__(self, cfg):
    self.entity = "RPMContentViewFilter"
    super().__init__(cfg)
    self.item.type = "rpm"
    self.item.original_packages = True
    self.item.inclusion = True
