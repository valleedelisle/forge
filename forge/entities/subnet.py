from ipaddress import ip_address

from forge.entities.base import Base


class Subnets(Base):
  def __init__(self, cfg, orgs=[]):
    self.entity = "Subnet"
    super().__init__(cfg, orgs=orgs)

  def create_all(self):
    for section in self._cfg.config:
      if section.startswith("subnets"):
        item = self.new_item()
        item.name = "-".join(section.split("-")[1:])
        item.__dict__.update(dict(self._cfg.config.items(section)))
        item.network_type = "IPv%s" % ip_address(str(
          item.network)).version
        item.organization = item.orgs
        item.location = item.locations
        item.domain = item.domains
        [delattr(item, k) for k in ["orgs", "locations", "domains"]]
        self.create(item, attribute_converter={"organization": "Org",
                                               "location": "Location",
                                               "domain": "Domains"})
