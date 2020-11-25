from forge.entities.base import Base


class DockerContentViewFilters(Base):
  """Forged DockerContentViewFilter object.
  Matches nailgun.entity.DockerContentViewFilter

  :param Base: forge.entities.Base
  :type Base: BaseClass
  :return: List of DockerContentViewFilter entities
  :rtype: list
  """
  def __init__(self, cfg, **kwargs):
    """Class initialization

    :param cfg: Configuration object
    :type cfg: forge.config
    """
    self.entity = "DockerContentViewFilter"
    super().__init__(cfg, **kwargs)
    self.item.type = "docker"
    self.item.inclusion = True
