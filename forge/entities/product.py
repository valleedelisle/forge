from re import sub

from logzero import logger as log

from forge.entities.base import Base
from forge.entities.repository import Repositories
from forge.entities.syncplan import SyncPlans
from alive_progress import alive_bar


class Products(Base):
  """Forged Product object.
  Matches nailgun.entity.Product

  Used mostly the container repos.

  :param Base: forge.entities.Base
  :type Base: BaseClass
  :return: List of Product entities
  :rtype: list
  """
  def __init__(self, cfg, org, name=None):
    self.entity = "Product"
    super().__init__(cfg, org)

  def generate_container_products(self, releases, sync):
    plans = SyncPlans(self._cfg, self.org).get_plan_map("weekly")
    inc = 0
    for release in releases:
      r = releases[release]
      if r["container"]:
        self._generate_container_repos(release, r, plans[inc % 5], sync)
      inc += 1

  def _generate_container_repos(self, release, r, sync_plan_id, sync):
    product = self.new_item()
    product.name = f"{release} containers"
    product.label = sub(r'[\s]+|\.', '_', product.name)
    product.sync_plan_id = sync_plan_id
    log.info(f"Creating product {product.name}")
    product = self.create(product)
    with alive_bar(len(r["containers"]),
      title=f"Creating product {product.name}") as bar:
      for container in r["containers"]:
        if not container.startswith(r["container_ceph_prefix"]):
          prefix = r["container_repo"]
        else:
          prefix = r["container_ceph_prefix"]
        self.log_bar(f"Creating {prefix}/{container}", bar)
        Repositories(self._cfg, self.org).create_container_repo(product.id,
                                           prefix, container)

    if sync:
      self.item.sync(synchronous=self._cfg.satellite.getboolean("async_sync"))
