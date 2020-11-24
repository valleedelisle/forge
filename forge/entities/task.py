from forge.entities.base import Base


class Tasks(Base):
  def __init__(self, cfg):
    self.entity = "ForemanTask"
    super().__init__(cfg)
