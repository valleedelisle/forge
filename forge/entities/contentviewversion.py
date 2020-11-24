from forge.entities.base import Base


class ContentViewVersions(Base):
  """Forged ContentViewVersion object.
  Matches nailgun.entity.ContentViewVersion

  :param Base: forge.entities.Base
  :type Base: BaseClass
  :return: List of ContentViewVersion entities
  :rtype: list
  """
  def __init__(self, cfg):
    """Class initialization

    :param cfg: Configuration object
    :type cfg: forge.config
    """
    self.entity = "ContentViewVersion"
    super().__init__(cfg)
