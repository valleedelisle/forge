from forge.actions.base import Base
from forge.entities.activationkey import ActivationKeys as ActivationKeysEntity
from forge.entities.organization import Org


class Activationkeys(Base):
  """ Satellite AK creation
  """
  def __init__(self, cfg, releases=[], zreleases=[]):
    super().__init__(cfg)
    self.org = Org(cfg, name=self._cfg.satellite["default_org"])
    self.aks = ActivationKeysEntity(cfg, self.org)
    self.aks.create_all(self.read_releases(releases, zreleases))
