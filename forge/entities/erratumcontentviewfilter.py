from forge.entities.base import Base


class ErratumContentViewFilters(Base):
  def __init__(self, cfg, **kwargs):
    self.entity = "ErratumContentViewFilter"
    super().__init__(cfg, **kwargs)
