import os
import re
from copy import deepcopy
from datetime import datetime
from re import sub
from tempfile import mkdtemp

import yaml
from alive_progress import alive_bar
from forge.actions.base import Base
from forge.entities.contentview import ContentViews
from forge.entities.organization import Org
from logzero import logger as log


class Containerprepare(Base):
  """ Generating container prepare templates
  as per this article:
  https://access.redhat.com/solutions/5171441
  """
  def __init__(self, cfg, releases=[], zreleases=[], output_dir=None, user=None,
               password=None):
    super().__init__(cfg)
    if not output_dir:
      output_dir = mkdtemp(prefix="container_prepare_templates")
    self.org = Org(cfg, name=self._cfg.satellite["default_org"])
    releases = self.read_releases(releases, zreleases)
    base = {'parameter_defaults': {'ContainerImagePrepare': []}}
    base_param = base["parameter_defaults"]
    registry_url = f"{self._cfg.satellite['host']}:5000"
    if user and password:
      base_param["ContainerImageRegistryCredentials"] = {
        registry_url: {
          user: password
        }
      }
      base_param["ContainerImageRegistryLogin"] = True
    base_param["DockerInsecureRegistryAddress"] = registry_url
    for release, r in releases.items():
      if r["container"]:
        cvs = ContentViews(self._cfg, self.org).get_by_releases(release,
                                                                zreleases)
        cvs = list(filter(lambda x: x.composite, cvs))
        self._build_repo_cache(cvs)
        log.info(f"Fetching all repo informations for content-views ({len(cvs)})")
        for z, containers in r["zstream"].items():
          cv = list(filter(lambda x: x.name.endswith(f"{release}-{z}"), cvs))
          if not len(cv):
            log.error(f"Unable to find CV for {release}-{z}")
            continue
          else:
            cv = cv[0]
            log.info(f"Checking repos in {cv.name}")
          content = deepcopy(base)
          clist = content["parameter_defaults"]["ContainerImagePrepare"]
          latest_tag = f"{release}{z}".replace("z", ".").replace("OSP", "")
          filename = f"container-image-prepare.{latest_tag}.yaml"
          template = os.path.join(output_dir, filename)
          if z == "latest":
            latest_tag = "latest"
          excludes = []
          # removing ceph
          noceph_containers = self.filter_containers(containers, 'openstack-|rhel')
          for container, tag in noceph_containers.items():
            log.debug(f"Container {container} Tag: {tag}")
            container_name = sub('^openstack-', '', container)
            excludes.append(container_name)
            repo = self.get_repo_by_name(cv, container_name)
            if repo:
              prefix = repo.container_repository_name.replace(container_name, "")
              clist.append({
                "includes": [container_name],
                "push_destination": False,
                "set": {
                  "name_prefix": prefix,
                  "name_suffix": '',
                  "namespace": self.get_namespace(repo),
                  "tag": tag
                }
              })
          ceph_container = self.filter_containers(containers,
                             r["container_ceph_prefix"])
          log.info(ceph_container)
          if len(ceph_container):
            ceph_name = list(ceph_container.keys())[0]
            ceph_tag = list(ceph_container.values())[0]
            ceph = self.get_repo_by_name(cv, ceph_name)
            ceph_image = ''
            if ceph:
              ceph_image = ceph.container_repository_name
          else:
            ceph_tag = ''
            ceph_image = ''
          namespace = self.get_namespace(repo)
          clist.append({
            "excludes": excludes,
            "push_destination": False,
            "set": {
              "ceph_image": ceph_image,
              "ceph_namespace": namespace,
              "ceph_tag": ceph_tag,
              "name_prefix": prefix,
              "name_suffix": '',
              "namespace": namespace,
              "tag": latest_tag
            }
          })
          now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
          with os.fdopen(os.open(template, os.O_CREAT | os.O_TRUNC | os.O_WRONLY,
                                 0o666), 'w') as f:
            f.write(f"# File {filename} was prepared by forge for OSP {release}{z}")
            f.write(f"# Generated on {now}")
            f.write("# https://github.com/valleedelisle/forge")
            yaml.dump(content, f, default_flow_style=False)

  def _build_repo_cache(self, cvs):
    self.repo_cache = {}
    for cv in cvs:
      log.info(f"{cv.name} has {len(cv.repository)} repositories to fetch metadata")
      self.repo_cache[cv.id] = []
      with alive_bar(len(cv.repository)) as bar:
        for repo in cv.repository:
          self.repo_cache[cv.id].append(repo.read())
          bar(f"Got {self.repo_cache[cv.id][-1].name}")

  def get_repo_by_name(self, cv, name):
    namespaces = list(filter(lambda x: x.name == name,
                                   self.repo_cache[cv.id]))
    if not len(namespaces):
      log.warning(f"Unable to find container {name} in repos"
                  f" for {cv.name}")
      return None
    return namespaces[0]

  def filter_containers(self, containers, name_pattern):
    return dict(filter(lambda x: re.match(name_pattern, x[0]), containers.items()))

  def get_namespace(self, repo):
    return repo.full_path.split("/")[0]
