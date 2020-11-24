from logzero import logger as log

from forge.entities.base import Base


class LifecycleEnvironments(Base):
  """Forged LifecycleEnvironment object.
  Matches nailgun.entity.LifecycleEnvironment

  :param Base: forge.entities.Base
  :type Base: BaseClass
  :return: List of LifecycleEnvironment entities
  :rtype: list
  """
  def __init__(self, cfg, org):
    """Class initialization

    :param cfg: Configuration object
    :type cfg: forge.config
    :param org: forged Org object
    :type org: forge.entities.Org
    """
    self.entity = "LifecycleEnvironment"
    super().__init__(cfg, org)

  def create_all(self):
    for section in self._cfg.config:
      if section.startswith("environments"):
        self.get_all()
        config = dict(self._cfg.config.items(section))
        item = self.new_item()
        item.label = "-".join(section.split("-")[1:])
        item.name = config["name"]
        prior = self.find(config["prior"])
        if not prior:
          log.error("Unable to find prior {prior} for {name}, skipping.")
          continue
        item.prior_id = prior.id
        self.create(item)
