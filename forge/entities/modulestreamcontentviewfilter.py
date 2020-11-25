from forge.entities.base import Base


class ModuleStreamContentViewFilters(Base):
  """Forged ModuleStreamContentViewFilter object.
  Matches nailgun.entity.ModuleStreamContentViewFilter

  :param Base: forge.entities.Base
  :type Base: BaseClass
  :return: List of ModuleContentViewFilter entities
  :rtype: list
  """
  def __init__(self, cfg, **kwargs):
    """Class initialization

    :param cfg: Configuration object
    :type cfg: forge.config
    """
    self.entity = "ModuleStreamContentViewFilter"
    super().__init__(cfg, **kwargs)
    self.item.type = "modulemd"
    self.item.original_module_streams = True
    self.item.inclusion = True
