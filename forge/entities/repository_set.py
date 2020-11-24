from logzero import logger as log

from forge.entities.base import Base
from requests.exceptions import HTTPError
from alive_progress import alive_bar
from forge.entities.syncplan import SyncPlans

import json


class RepositorySets(Base):
  def __init__(self, cfg, org):
    self.entity = "RepositorySet"
    # Caching
    self._repos = {}
    super().__init__(cfg, org)

  def get_by_labels(self, labels, rh_repo=False):
    """ This returns the repo object based on label searched"""
    log.debug(f"Looking for {labels}")
    repos = []
    with alive_bar(len(labels),
      title="Fetching reposets data") as bar:
      for label in labels:
        self.log_bar(f"Looking for {label}", bar)
        if label in self._repos:
          repo = self._repos[label]
        else:
          repo = self.search(None, label=label)
          if len(repo) == 0:
            log.error(f"Repository labeled {label} is not found. Skipping")
            continue
          if not rh_repo:
            self._repos[label] = [r.read() for r in repo[0].repositories]
          else:
            self._repos[label] = repo
        repos.append(self._repos[label][0])
    return repos

  def get_enabled(self):
    self.get_all()
    return list(filter(lambda x: len(x.repositories), self.items))

  def enable_all(self, sync=False):
    sync_plans = SyncPlans(self._cfg, self.org)
    plan_map = sync_plans.get_plan_map("daily")
    planinc = 0

    for section in self._cfg.config:
      if section.startswith("products"):
        self.get_all(True)
        config_keys = dict(self._cfg.config.items(section))
        log.debug(config_keys)
        products = json.loads(config_keys["list"])
        multiplier = 5 if sync else 4
        repos = self.get_by_labels(list(map(lambda x: x["repository_set"],
          products)), True)
        with alive_bar(len(products) * multiplier,
          title="Enabling repo-sets") as bar:
          for i in products:
            self.log_bar(f"Getting reposet {i['repository_set']}", bar)
            filtered_repos = list(filter(lambda x: x.label == i["repository_set"],
              repos))
            log.debug(f"Filtered repos: {filtered_repos}")
            if not len(filtered_repos):
              log.warning(f"Skipping {i['repository_set']}")
              for x in range(multiplier - 1):
                bar("Skipping")
              continue
            repo = filtered_repos[0]
            self.log_bar(f"Looking for repo-set: {repo.label}", bar)
            if len(repo.repositories) == 0:
              attributes = {"basearch": config_keys["arch"],
                            "organization_id": self.org.item.id}
              if "releasever" in i:
                attributes["releasever"] = i["releasever"]
              log.debug(f"Enabling {self.entity} {attributes}")
              try:
                self.log_bar(f"Enabling {repo.label}", bar)
                repo.enable(data=attributes)
              except HTTPError as err:
                if err.response.status_code == 409:
                  log.warning(f"{self.entity} {repo.label} already enabled...")
                else:
                  log.error(f"Error creating {self.entity}: "
                            f"{err.response.status_code} {err.response._content}")
            else:
              log.debug("Repository {repo.label} already enabled")
              self.log_bar(f"Skipped {repo.label}", bar)
            self.log_bar("Updating sync plan", bar)
            if "daily" in i["sync_plan"]:
              planinc += 1
              plan_id = plan_map[planinc % 6]
            else:
              plan_id = sync_plans.get(i["sync_plan"]).id
            repo.product.sync_plan_id = plan_id
            repo.product.update()
            if sync:
              self.log_bar(f"Syncing {repo.label}", bar)
              repo.product.sync(
                synchronous=self._cfg.satellite.getboolean("async_sync"))
