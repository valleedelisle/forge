#!/usr/bin/env python3.8
from logging import DEBUG, INFO

import click
import logzero
from alive_progress import config_handler
from forge.config import Config, load_module
"""
Satellite installation and configuration wrapper
Edit sat.cfg before running this
# Running the installation:
forge.py install
# Running the initialization:
forge.py make init
# Checking sync
forge.py check sync

More information: forge.py --help
"""

__author__ = "David Vallee Delisle"
__version__ = "0.1.0"
__license__ = "MIT"

global log
global cfg
install_tasks = ["pkg-install", "satellite-install", "set-default-org",
                 "set-default-loc", "manifest-upload", "manifest-refresh",
                 "insights-client-install", "insights-client-register"]

config_handler.set_global(bar="bubbles", spinner="dots_waves2")


def releases_filters(function):
  function = click.option("-r", "--stack-releases", "releases", multiple=True,
                          type=click.Choice(['OSP10', 'OSP13', 'OSP16.1'],
                          case_sensitive=False),
                          help="OpenStack Releases")(function)
  return function


def zreleases_filters(function):
  function = click.option("-z", "--z-releases", "zreleases", multiple=True,
                          type=click.Choice(["GA", "latest"]
                                             + [f"z{i}" for i in range(1, 20)],
                          case_sensitive=False),
                          help="OpenStack Z Releases")(function)
  return function


@click.group()
@click.option("-v", "--verbose", is_flag=True,
              help="Will print debug messages.")
@click.option("-c", "--config-file", default="sat.cfg", show_default=True,
              help="Configuration file")
@click.option("-s", "--satellite-server", default=None,
              help="Satellite server name to work on")
def cli(verbose, config_file, satellite_server=None):
  global log
  global cfg
  log_level = DEBUG if verbose else INFO
  formatter = logzero.LogFormatter(datefmt='%Y-%m-%d %H:%M:%S')
  logzero.setup_default_logger(level=log_level, formatter=formatter,
                               logfile="sat.log")
  cfg = Config(config_file)
  cfg.read_config(satellite_server)
  logzero.setup_default_logger(level=log_level, formatter=formatter)
  # We want to log debug to file, but info to screen, unless -v
  logzero.logfile(f"{cfg.satellite['name']}.log", loglevel=DEBUG)
  log = logzero.logger
  pass


@cli.command(help="Installs satellite on the local system")
@click.option("-s", "--skip", "skip_tasks", multiple=True,
              type=click.Choice(install_tasks, case_sensitive=False),
              help="Skip tasks")
@click.option("-o", "--only", "only_tasks", multiple=True,
              type=click.Choice(install_tasks, case_sensitive=False),
              help="Only execute these tasks")
def install(skip_tasks=[], only_tasks=[]):
  log.info("Running satellite-installer")
  load_module("install", "install")(cfg, skip_tasks, only_tasks)


@cli.group(help="Generates and creates various components")
def make():
  pass


@make.command(help="""Initializes the satellite server with some sync plans,
                      lifecycle environments and some default settings as
                      defined in the config file""")
def init():
  log.info("Initializaing satellite")
  load_module("make", "init")(cfg)


@make.command(help="Enables the required repository-sets")
@click.option("-s", "--sync", is_flag=True,
              help="Also sync the products after enabling")
def repo_sets(sync):
  log.info("Enabling reposets")
  load_module("make", "reposets")(cfg, sync)


@make.command(help="Generates the products and repositories based on the "
                   " configuration")
@releases_filters
@click.option("-s", "--sync", is_flag=True, default=False,
              help="Also sync the products after addition")
def container_repos(sync, releases):
  log.info("Generating products and adding repos")
  load_module("make", "containerrepos")(cfg, sync, releases)


@make.command(help="Creates the Activation Keys")
@releases_filters
def activation_keys(releases):
  log.info("Creating Activation Keys")
  load_module("make", "activationkeys")(cfg, releases)


@make.command(help="Generates the container-prepare template")
@releases_filters
@zreleases_filters
@click.option("-o", "--output-dir",
              help="Output directory where to store the files")
@click.option("-u", "--user", help="Username")
@click.option("-p", "--password", help="Password")
def container_prepare(releases, zreleases, output_dir, user, password):
  log.info("Generating container prepare templates")
  load_module("make", "containerprepare")(cfg, releases, zreleases, output_dir,
                                          user, password)


@make.command(name="content-views",
              help="Generates the content-views based on the configuration")
@click.option("-p", "--promote-only", is_flag=True, default=False,
              help="Don't create CVs, just promote latest version")
@click.option("-c", "--composite-only", is_flag=True, default=False,
              help="Don't create CVs, just create CCVs and promote them")
@click.option("-f", "--force", is_flag=True, default=False,
              help="Force creation even if there's running tasks")
@releases_filters
@zreleases_filters
def make_cvs(promote_only, composite_only, releases, zreleases, force):
  log.info("Generating content-views")
  load_module("make", "contentviews")(cfg, promote_only, composite_only, releases,
                                      zreleases, force)


@cli.group(help="Performs various validations and verification")
def check():
  pass


@check.command(help="Returns the sync status for all repos")
def sync():
  log.info("Checking sync status")
  load_module("check", "sync")(cfg)


@check.command(help="Searches the repository-sets")
@click.option("-t", "--type", "repo_type",
              type=click.Choice(['docker', 'yum'], case_sensitive=False),
              help="Repo Type")
@click.option("-e", "--enabled", is_flag=True,
              help="Returns only enabled repos")
@click.option("--label",
              help="Repository set label (ie: rhel-7-server-openstack-10-rpms)")
def repos(repo_type, enabled, label):
  load_module("check", "reposet")(cfg, repo_type, enabled, label)


@check.command(name="content-views", help="Searches the Content Views")
@click.option("-d", "--delete", is_flag=True,
              help="Delete content-views")
@click.option("-m", "--match", help="Match pattern to filter")
def check_cvs(delete, match):
  load_module("check", "contentview")(cfg, delete, match)


@check.command(help="Task manipulation")
@click.option("--id", help="Returns information about Foreman Task ID")
@click.option("-i", "--incomplete", is_flag=True,
              help="Returns incompleted tasks")
@click.option("-b", "--bad", is_flag=True,
              help="Returns non-succesfull tasks")
@click.option("-r", "--reset-pulp", help="Reset pulp tasks for Foreman Task")
def task(id, incomplete, bad, reset_pulp):
  if id:
    load_module("check", "task")(cfg).get_by_id(id)
  elif incomplete:
    load_module("check", "task")(cfg).get_incompletes()
  elif bad:
    load_module("check", "task")(cfg).get_bads()
  elif reset_pulp:
    load_module("check", "task")(cfg).reset_pulp_task(reset_pulp)


if __name__ == "__main__":
  cli()
# vim: et sts=2 sw=2 ts=2
