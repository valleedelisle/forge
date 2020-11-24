from logging import DEBUG, ERROR, INFO, WARN  # noqa: F401
import os
import re
import socket
import subprocess
import sys
import time

from logzero import logger as log
import requests
from requests.exceptions import HTTPError

from forge.actions.base import Base


class Install(Base):
  """ Satellite Installation
  This is where we run the installation process
  Tasks executed:
  - Validating host environment
  - Installing missing packages
  - Running the satellite-installer command
  - Uploading and refreshing a manifest
  - Installing the insights-client
  """
  def __init__(self, cfg, skip_tasks = [], only_tasks = []):
    self.register_insights = False
    self.manifest = None
    self.pgid = None
    self.task = None
    super().__init__(cfg)
    self.skip_tasks = skip_tasks
    self.only_tasks = only_tasks
    self.set_defaults(["manifest", "register_insights", "host", "username",
                       "password"])
    if socket.gethostname() != self.host:
      log.error("Install action requires to be run on the satellite server and "
                "can't be run remotely. Local system: %s Satellite Host: %s"
                % (socket.gethostname(), self.host))
      sys.exit(-1)
    # We need to remove python1 from the env, otherwise the satellite installer
    # fails.
    # https://access.redhat.com/solutions/5248249
    self.env = os.environ.copy()
    self.env["PATH"] = ":".join(list(filter(lambda x: ".python" not in x,
                                            self.env["PATH"].split(":"))))
    # We need to make sure our IP is in /etc/hosts because satellite does a reverse
    # lookup on that IP.
    if len(self.skip_tasks):
      log.warning(f"Skipping these tasks: {skip_tasks}")
    if len(self.only_tasks):
      log.warning(f"Only these tasks: {only_tasks}")
    self.check_host_file()
    self.install_packages()
    self.install_satellite()
    self.set_hammer_defaults()
    if self.manifest:
      self.get_manifest()
      self.upload_manifest()
      self.refresh_manifest()
    if self.register_insights:
      self.install_insights_client()
      self.register_insights_client()
    log.info("Satellite installation process completed")

  def test_sh(self):
    """
    Test function to validate subprocess
    """
    if self.run(["./test.sh"], "test.sh"):
      self.checkout("Do you want to proceed")

  def check_host_file(self):
    """
    Host file validation, if our host is not in there
    we add it.
    """
    my_ip = socket.gethostbyname(socket.gethostname())
    with open("/etc/hosts", "r+") as host_file:
      for line in host_file:
        if re.search(rf"^{my_ip}.*{self.host}", line, re.IGNORECASE):
          break
      else:
        log.debug(f"Host entry not found, adding {my_ip} for {self.host}")
        host_file.write(f"{my_ip}\t{self.host}\n")

  def install_packages(self):
    """
    Installing packages
    """
    cmd = ["yum", "-y", "install", "satellite"]
    if self.register_insights:
      cmd.append("insights-client")
    if self.run(cmd, "pkg-install"):
      self.checkout()

  def install_satellite(self):
    """
    Running the satellite-installer
    """
    cmd = ["satellite-installer", "--scenario", "satellite", "-v",
           "--foreman-logging-level", "debug",
           "--foreman-initial-admin-password", self.password,
           "--foreman-initial-admin-username", self.username]
    if self.default_org:
      cmd.extend(["--foreman-initial-organization", self.default_org])
    if self.default_location:
      cmd.extend(["--foreman-initial-location", self.default_location])
    if self.run(cmd, "satellite-install"):
      self.checkout()

  def set_hammer_defaults(self):
    """
    Setting the defaults org and location for easier management later
    """
    if self.default_org and self.run(["hammer", "defaults", "add", "--param-name",
                                      "oraganization", "--param-value",
                                      self.default_org], "set-default-org"):
      self.checkout()
    if self.default_location and self.run(["hammer", "defaults", "add",
                                           "--param-name", "location",
                                           "--param-value", self.default_location],
                                           "set-default-loc"):
      self.checkout()

  def get_manifest(self):
    """
    Downloading the manifest
    """
    log.info("Downloading manifest file %s" % self.manifest)
    time_start = time.time()
    try:
      r = requests.get(self.manifest, allow_redirects=True)
      r.raise_for_status()
    except HTTPError as http_err:
      log.error(f'HTTP error occurred: {http_err}')
    except Exception as err:
      log.error(f'Other error occurred: {err}')
    else:
      duration = time.time() - time_start
      log.info("Downloaded succesfully in %.0f seconds" % duration)
    if r.headers.get('content-type') == "application/zip":
      self.manifest_file = "/tmp/%s" % self.manifest.split('/')[-3]
      try:
        os.remove(self.manifest_file)
      except OSError:
        pass
      open(self.manifest_file, 'wb').write(r.content)
    else:
      log.error("Invalid manifest file %s - Type: %s - We're looking for a zip file"
                "here." % (self.manifest, r.headers.get('content-type')))
      sys.exit(-1)

  def upload_manifest(self):
    if self.run(["hammer", "subscription", "upload", "--file", self.manifest_file,
                 "--organization", self.default_org], "manifest-upload"):
      self.checkout()

  def refresh_manifest(self):
    if self.run(["hammer", "subscription", "refresh-manifest", "--organization",
                 self.default_org], "manifest-refresh"):
      self.checkout()

  def install_insights_client(self):
    if self.run(["satellite-maintain", "packages", "install", "insights-client"],
                "insights-client-install"):
      self.checkout("Do you want to proceed")

  def install_pulpadmin(self):
    pulpversion, err = subprocess.Popen(['rpm', '-qa', "pulp-server",
      "--queryformat", "%{VERSION}"], stdout=subprocess.PIPE,
      stderr=subprocess.PIPE).communicate()
    if self.run(["yum", "-y", "install", f"pulp-admin-client-{pulpversion}",
      "pulp-rpm-admin-extensions.noarch", "--disableplugin=foreman-protector"],
      "pulpadmin-install"):
      self.checkout()

  def register_insights_client(self):
    if self.run(["insights-client", "--register"], "insights-client-register"):
      self.checkout()
