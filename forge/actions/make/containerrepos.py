from logzero import logger as log

from forge.actions.base import Base
from forge.entities.organization import Org
from forge.entities.product import Products


class Containerrepos(Base):
  """ Satellite product creation
  """
  def __init__(self, cfg, sync=False, releases=[]):
    super().__init__(cfg)
    if sync:
      log.warning("A sync of the product will be started upon creation")
    self.org = Org(cfg, name=self._cfg.satellite["default_org"])
    log.info("Creating Container products with repositories")
    container_product = Products(self._cfg, self.org)
    container_product.generate_container_products(self.read_releases(releases),
       sync)
