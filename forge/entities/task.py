from forge.entities.base import Base


class Tasks(Base):
  """Forged Task object.
  Matches nailgun.entity.ForemanTask

  :param Base: forge.entities.Base
  :type Base: BaseClass
  :return: List of ForemanTask entities
  :rtype: list
  """
  def __init__(self, cfg):
    self.entity = "ForemanTask"
    super().__init__(cfg)
