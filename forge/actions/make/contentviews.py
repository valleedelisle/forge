from forge.actions.base import Base
from forge.entities.contentview import ContentViews as ContentViewEntity
from forge.entities.organization import Org


class Contentviews(Base):
  """ Satellite product creation
  """
  def __init__(self, cfg, promote_only=False, composite_only=False, releases=[],
               zreleases=[], force=False):
    super().__init__(cfg)
    self.org = Org(cfg, name=self._cfg.satellite["default_org"])
    self.cvs = ContentViewEntity(cfg, self.org)
    release_list = self.read_releases(releases, zreleases)
    self.cvs.create_all(release_list, promote_only, composite_only, force)
