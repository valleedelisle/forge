from forge.entities.base import Base


class RPMContentViewFilters(Base):
  def __init__(self, cfg):
    self.entity = "RPMContentViewFilter"
    super().__init__(cfg)
