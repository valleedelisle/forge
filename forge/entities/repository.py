from forge.entities.base import Base


class Repositories(Base):
  def __init__(self, cfg, org):
    self.entity = "Repository"
    super().__init__(cfg, org)

  def get_containers(self, r):
    """ Returns all the repos of type docker for the product """
    return self.search(None, **{"content_type": "docker",
                                "product_name": f"{r} containers"})

  def create_container_repo(self, product_id, prefix, container):
    upstream = self._cfg.config["upstream-registry"]
    item = self.new_item()
    item.product_id = product_id
    item.content_type = "docker"
    item.url = upstream["url"]
    item.docker_upstream_name = f"{prefix}/{container}"
    item.upstream_username = upstream["username"]
    item.upstream_password = upstream["password"]
    item.organization = self.org
    item.name = container.replace("openstack-", "")
    self.create(item)
