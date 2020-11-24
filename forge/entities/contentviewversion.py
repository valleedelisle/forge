from forge.entities.base import Base


class ContentViewVersions(Base):
  """ Satellite Content-views creation
  This is where we generate the content-views
  """
  def __init__(self, cfg, id):
    self.entity = "ContentViewVersion"
    super().__init__(cfg, id=id)
