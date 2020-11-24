from forge.actions.base import Base
from forge.entities.domain import Domains
from forge.entities.lifecycle_environment import LifecycleEnvironments
from forge.entities.organization import Org
from forge.entities.setting import Settings
from forge.entities.subnet import Subnets
from forge.entities.syncplan import SyncPlans


class Init(Base):
  """ Satellite initialization
  This should be executed after satellite is installed.
  Resources created:
  = settings
  - sync-plans
  - lifecycle-environments
  - domains
  - subnets
  """
  def __init__(self, cfg):
    super().__init__(cfg)
    self.org = Org(cfg, name=self._cfg.satellite["default_org"])
    self.settings = Settings(cfg)
    self.settings.set_all()
    self.syncplans = SyncPlans(cfg, self.org)
    self.syncplans.create_all()
    self.environments = LifecycleEnvironments(cfg, self.org)
    self.environments.create_all()
    self.domains = Domains(cfg, orgs=[self.org])
    self.domains.create_all()
    self.subnets = Subnets(cfg, orgs=[self.org])
    self.subnets.create_all()
