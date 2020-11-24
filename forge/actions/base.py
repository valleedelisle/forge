from datetime import datetime as dt
import time
import re
import subprocess
import os
import selectors
import sys

from logzero import logger as log

ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
log_regex = (r"\[ (?P<level>INFO|WARN|ERROR|DEBUG) [\d]{4}-[\d]{1,2}-[\d]{1,2}"
             r"[T\s][\d]{1,2}:[\d]{1,2}:[\d]{2} verbose\] (?P<line>.*)")

sat_log = re.compile(log_regex)


class Base(object):
  col = {
    'R': "\033[0;31;40m",  # RED
    'G': "\033[0;32;40m",  # GREEN
    'Y': "\033[0;33;40m",  # Yellow
    'B': "\033[0;34;40m",  # Blue
    'N': "\033[0m"  # Reset
  }

  def __init__(self, cfg):
    self._cfg = cfg
    self.set_defaults(["default", "default_org", "default_location"])

  def set_defaults(self, def_list):
    for default in def_list:
      try:
        setattr(self, default, self._cfg.satellite[default])
      except KeyError:
        setattr(self, default, None)

  def color_by_name(self, status, string=None):
    status.lower()
    if status == "success":
      color = self.col['G']
    elif status == "warning":
      color = self.col['Y']
    elif status == "pending":
      color = self.col['B']
    else:
      color = self.col['R']
    if not string:
      return color
    return color + str(string) + self.col['N']

  def get_duration(self, start, end):
    duration = None
    try:
      duration = dt.fromisoformat(end[:-1]) - dt.fromisoformat(start[:-1])
    except ValueError:
      ts_format = "%Y-%m-%d %H:%M:%S %Z"
      duration = dt.strptime(end, ts_format) - dt.strptime(start, ts_format)
    except TypeError:
      duration = "N/A"
    return duration


  def read_releases(self, stack_releases=[], zreleases=[]):
    """ Generates a releases dict based on config cvs, containertags and zdates
    """
    releases = {}
    for section in self._cfg.config:
      if "-" in section:
        release = section.split("-")[1]
      else:
        continue
      if section.startswith("cvs-"):
        releases[release] = dict(self._cfg.config.items(section))
        r = releases[release]
        r["container"] = self._cfg.config[section].getboolean("container")
      elif (section.startswith("zdates-") and (not len(stack_releases)
            or release in stack_releases)):
        r = releases[release]
        if "zdates" not in r:
            r["zdates"] = {"latest": "latest"}
        for zstream, date in self._cfg.config[section].items():
          if not len(zreleases) or zstream in zreleases:
            r["zdates"][zstream] = date
      elif section.startswith("containertags"):
        r = releases[release]
        zstream = section.split("-")[2]
        if "containers" not in r:
          r["containers"] = []
        if "zstream" not in r:
          r["zstream"] = {}
        if (zstream not in r["zstream"]
            and (not len(zreleases) or zstream in zreleases)):
          r["zstream"][zstream] = {}
        for container, tag in self._cfg.config[section].items():
          if container not in r["containers"]:
            r["containers"].append(container)
          if not len(zreleases) or zstream in zreleases:
            if container not in r["zstream"][zstream]:
              r["zstream"][zstream][container] = tag
            else:
              log.warning(f"Duplicate container in section {section} for "
                          f"container {container}: {tag} and "
                          f"{r['zstream'][zstream][container]}. We're using "
                          "the latter.")
    if len(stack_releases):
      releases = {k: v for k, v in releases.items() if k in stack_releases}
    return releases

  def get_item_ids(self, items):
    """ Converts a lit of objects into a list of IDs"""
    return list(map(lambda x: x.id, items))

  def run(self, command, task_name):
    if (task_name in self.skip_tasks
        or (len(self.only_tasks)
        and task_name not in self.only_tasks)):
        return False
    self.task_name = task_name
    log.info("Starting task %s" % task_name)
    self.task_start = time.time()
    self.task = subprocess.Popen(command,
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 preexec_fn=os.setsid, env=self.env)
    self.sel = selectors.DefaultSelector()
    self.sel.register(self.task.stdout, selectors.EVENT_READ)
    self.sel.register(self.task.stderr, selectors.EVENT_READ)
    self.pgid = os.getpgid(self.task.pid)
    log.debug("Task started with pid %s" % self.pgid)
    return True

  def _format_out(self, lines, level=None):
    lines = ansi_escape.sub('', lines)
    for line in lines.splitlines():
      s = re.search(sat_log, line)
      if s:
        log_level = s.groupdict()["level"] if not level else level
        line = s.groupdict()["line"]
      else:
        log_level = "INFO" if not level else level
      log.log(globals()[log_level], line)

  def checkout(self, prompt=None):
    while self.task.poll() is None:
      for key, val in self.sel.select():
        line = key.fileobj.read1().decode()
        line = line.strip()
        if key.fileobj is self.task.stdout:
          self._format_out(line)
        else:
          self._format_out(line, "ERROR")
        if prompt and prompt in line:
          log.debug("Prompt in line, sending yes")
          self.task.stdin.write("y\n".encode("utf-8"))
          self.task.stdin.flush()
    self.task_end = time.time()
    self.task_duration = self.task_end - self.task_start
    if self.task.returncode == 0:
      log.info("Task completed succesfully in %.0f seconds" % self.task_duration)
    else:
      log.error("Task failed with returncode %s in %.0f seconds"
                % (self.task.returncode, self.task_duration))
      sys.exit(-1)
