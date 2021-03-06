from json import dumps

from prettytable import PrettyTable

from forge.actions.base import Base
from forge.entities.contentview import ContentViews as ContentViewEntity
from forge.entities.activationkey import ActivationKeys
from forge.entities.organization import Org
from logzero import logger as log
from alive_progress import alive_bar


class Contentview(Base):
  def __init__(self, cfg, delete=False, match=None):
    super().__init__(cfg)
    self.org = Org(cfg, name=self._cfg.satellite["default_org"])
    cvs = ContentViewEntity(cfg, self.org)
    search_string = {"per_page": 10000}
    if match:
      search_string["operator"] = "like"
      search_string["name"] = match
    log.info(f"Search pattern: {search_string}")
    items = cvs.search(cvs.item, **search_string)
    items.sort(key=lambda x: x.composite, reverse=True)
    x = PrettyTable()
    x.field_names = ["ID", "Label", "Version", "Repositories", "Last Published"]
    x.max_width["Version"] = 80
    number_of_versions = sum([len(c.version) for c in items])
    ak = ActivationKeys(self._cfg, self.org)
    with alive_bar(number_of_versions,
      title="Getting CV version information") as bar:
      for c in items:
        versions = []
        if delete:
          log.info(f"Deleting activation keys for {c.name}")
          for aks in ak.get_by_cv(c):
            aks.delete()
        for version in c.version:
          vd = version.read_json()
          bar(f"Got {c.name} {vd['version']}")
          if len(vd["environments"]):
            versions.extend(list(map(lambda x: f"{x['name']} "
                                               f"Host: {x['host_count']}, "
                                               f"AK: {x['activation_key_count']}",
                                     vd["environments"])))
            versions.extend([f"version: {vd['version']}",
                             f"updated: {vd['updated_at']}",
                             f"package_count: {vd['package_count']}"])
            if delete:
              for env in vd["environments"]:
                log.info(f"Deleting from {env['name']}")
                c.delete_from_environment(env["id"], synchronous=True)
              version.delete()
        if delete:
          c.delete()
        x.add_row([c.id, c.label, dumps(versions, sort_keys=True, indent=2),
                   self.get_item_ids(c.repository), c.last_published])
    print(x)
