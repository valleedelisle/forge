from forge.entities.base import Base


class ErratumContentViewFilters(Base):
  """Forged ErratumContentViewFilter object.
  Matches nailgun.entity.ErratumContentViewFilter

  :param Base: forge.entities.Base
  :type Base: BaseClass
  :return: List of ErratumContentViewFilter entities
  :rtype: list
  """
  def __init__(self, cfg, **kwargs):
    """Class initialization

    :param cfg: Configuration object
    :type cfg: forge.config
    """
    self.entity = "ErratumContentViewFilter"
    super().__init__(cfg, **kwargs)
    self.item.inclusion = True
    self.item.type = "erratum"
