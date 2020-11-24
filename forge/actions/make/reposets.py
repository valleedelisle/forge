from logzero import logger as log

from forge.actions.base import Base
from forge.entities.organization import Org
from forge.entities.repository_set import RepositorySets


class Reposets(Base):
  """ Satellite product creation
  """
  def __init__(self, cfg, sync=False):
    super().__init__(cfg)
    if sync:
      log.warning("A sync of the product will be started upon creation")
    self.org = Org(cfg, name=self._cfg.satellite["default_org"])
    log.info("Enabling RepositorySets")
    reposet = RepositorySets(cfg, self.org)
    reposet.enable_all(sync)
