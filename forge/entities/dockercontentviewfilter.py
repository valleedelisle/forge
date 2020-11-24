from forge.entities.base import Base


class DockerContentViewFilters(Base):
  def __init__(self, cfg, **kwargs):
    self.entity = "DockerContentViewFilter"
    self.type = "docker"
    super().__init__(cfg, **kwargs)
