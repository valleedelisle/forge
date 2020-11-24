import re
from json import dumps
from os import path
from time import sleep

from forge.config import load_module
from logzero import logger as log
from nailgun import entities, entity_mixins
from requests import request
from requests.exceptions import HTTPError


class Base(object):
  """Base object used for all forged entities
  """
  def __init__(self, cfg, org=None, orgs=[], **kwargs):
    """Class initialization

    :param cfg: [description]
    :type cfg: [type]
    :param org: forged Org entity
    :type org: forge.entities.Org
    :param orgs: list of forged Org entities, used for entites that can be part of
                 multiple organizations
                 defaults to []
    :type orgs: list, optional
    """
    self.items = []
    self.org = org
    self.orgs = orgs
    self._cfg = cfg
    if not hasattr(self, "_forbidden_keys"):
      self._forbidden_keys = []
    if not hasattr(self, "_pass_to_new"):
      self._pass_to_new = []
    if not hasattr(self, "_search_key"):
      self._search_key = "name"
    if not hasattr(self, "entity"):
      self.entity = ""

    log.debug(f"Loaded {self.entity} {kwargs}")
    try:
      self.name = kwargs["name"]
    except KeyError:
      self.name = None
    # Let's create an entity to benefit from it's functions
    self.item = self.new_item()
    if "version" in kwargs:
      self.item = self.get(kwargs["version"], "version")
      log.error(self.item)

  def log_item(self, action, item, msg=None):
    """Logs an action on an item in a specific and generic format

    :param action: Action executed on an item (ex: create, update, delete)
    :type action: str
    :param item: Forged entity
    :type item: forge.entities.object
    :param msg: Message to log, defaults to None
    :type msg: str, optional
    """
    try:
      log_msg = f"{action} {self.entity} {item.name}"
    except AttributeError:
      log_msg = f"{action} {self.entity} {item}"
    if msg:
      log_msg += f": {msg}"
    log.debug(log_msg)

  def log_bar(self, msg, bar):
    """Debug logging alive-progress bar messages

    :param msg: Message to log and pass to the bar
    :type msg: str
    :param bar: Alive progress bar context
    :type bar: context
    """
    log.debug(msg)
    bar(msg)

  def _raw_req(self, method, endpoint, data={}):
    """Send a raw request to the satellite API

    :param method: HTTP Verb to use (ex: get, post, put, delete)
    :type method: str
    :param endpoint: endpoint to hit (ex: /content_views/{cv.id}/filters)
    :type endpoint: str
    :param data: data to pass, defaults to {}
    :type data: dict, optional
    :return: Result key from the response
    :rtype: dict
    """
    data["per_page"] = 1000
    response = request(method,
        f'{self._cfg.server_config.url}/katello/api/v2/{endpoint}',
        data=dumps(data),
        auth=self._cfg.server_config.auth,
        headers={"content-type": "application/json"},
        verify=self._cfg.server_config.verify,
    )
    response.raise_for_status()
    decoded = response.json()
    return decoded["results"]

  def new_item(self, **kwargs):
    """Generates an entity item.

    :param kwargs: initialization keys
    :return: Nailgun Entity item
    :rtype: nailgun.entities.item
    """
    # Used mostly for ContentViewFilterRules that require a ContentViewFilter
    # object during initialization.
    if len(self._pass_to_new):
      new_args = {x: getattr(self, x) for x in self._pass_to_new}
      kwargs = {**new_args, **kwargs}
    item = getattr(entities, self.entity)
    if self.org:
      return item(self._cfg.server_config, organization=self.org.item)
    if len(self.orgs) > 0:
      return item(self._cfg.server_config,
                  organization=list(map(lambda x: x.item, self.orgs)))
    if len(kwargs):
      return item(self._cfg.server_config, **kwargs)
    return item(self._cfg.server_config)

  def get_all(self, full=False, key_name=None, value=None):
    """Populates a cached list of all items

    :param full: sets the "full_result" key on the search, defaults to False
    :type full: bool, optional
    :param key_name: Add a search filter on key, defaults to None
    :type key_name: str, optional
    :param value: Value to filter key_name on, defaults to None
    :type value: str, optional
    :return: List of cached items
    :rtype: list, nailgun.entities.item
    """
    search_string = {}
    if key_name and value:
      search_string[key_name] = value
    if full:
      search_string["full_result"] = full
    self.items = self.search(None, **search_string)
    return self.items

  def find(self, value, key_name="name"):
    """Search the cache and returns the first item matching criterium

    :param value: Value to look for, normally it's by name
    :type name: str
    :param key_name: Key to search on, defaults to "name"
    :type key_name: str, optional
    :return: Nailgun entity
    :rtype: nailgun.entities.item or None
    """
    for item in self.items:
      if getattr(item, key_name) == value:
        return item
    else:
      log.warn(f"Item {self.entity} with key {key_name} = {value} not found")
      return None

  def find_or_new(self, name, key_name="name"):
    """Search the cache and returns the first item matching criterium,
    or creates a new one if None is found.

    :param value: Value to look for, normally it's by name
    :type name: str
    :param key_name: Key to search on, defaults to "name"
    :type key_name: str, optional
    :return: Nailgun entity
    :rtype: nailgun.entities.item or new item
    """
    item = self.find(name, key_name)
    return item if item else self.new_item()

  def get(self, value, key_name="name"):
    """Search satellite in realtime to find an entity matching the key/value
    and returns the first matching item.

    :param value: Value to look for, normally it's by name
    :type name: str
    :param key_name: Key to search on, defaults to "name"
    :type key_name: str, optional
    :return: Nailgun entity
    :rtype: nailgun.entities.item or new item
    """
    items = self.search(None, **{key_name: value})
    if not items:
      log.warning(f"Unable to get {self.entity} with {key_name} {value}")
      return None
    for item in items:
      if getattr(item, key_name) == value:
        return item
    return None

  def get_or_new(self, name):
    """Search satellite in realtime and returns the first item matching key/value,
    or creates a new one if None is found.

    :param value: Value to look for, normally it's by name
    :type name: str
    :param key_name: Key to search on, defaults to "name"
    :type key_name: str, optional
    :return: Nailgun entity
    :rtype: nailgun.entities.item or new item
    """
    item = self.get(name)
    return item if item else self.new_item().create()

  def search(self, item, **kwargs):
    """Wrapper around the search function.

    :param kwargs:
      "operator": Can be "not" to compare with "!=", otherwise "="
      "per_page": Number of items to return, defaults to 1000
      "full_result": Passed to the search query.
      anything else will be added to the search string.
    :param item: Use a specific entity to run the search
    :type item: nailgun.entities.item
    :return: List of items matching search query
    :rtype: list, nailgun.entities.item
    """
    if not item:
      item = self.new_item()
    if "full_result" in kwargs and not kwargs["full_result"]:
      del kwargs["full_result"]
    try:
      per_page = kwargs["per_page"]
      del kwargs["per_page"]
    except KeyError:
      per_page = 1000
    operator = " = "
    try:
      if kwargs["operator"] == "not":
        operator = " != "
      elif kwargs["operator"] == "like":
        operator = " ~ "
      del kwargs["operator"]
    except KeyError:
      pass
    # Takes kwargs, quote them if necessary and join them
    quoted_values = map(lambda x: '"' + str(x) + '"' if type(x) != int else str(x),
                        kwargs.values())
    search_string = " AND " .join(map(operator.join,
                                      dict(zip(kwargs, quoted_values)).items()))
    query = {'per_page': per_page, 'search': search_string}
    log.debug(f"Searching for {query} on {item}")
    try:
      return item.search(query=query)
    except HTTPError as err:
      log.error(f"Search Error {err.response.status_code}: "
                f"{err.response._content}")

  def nailrun(self, item, action, **kwargs):
    """ executes a CUD command on an entity

    :param item: Entity to run the command
    :type item: nailgun.entities.item
    :param action: Action to perform (create, update, delete)
    :type action: str
    :raises Exception: Unknown exception
    :return: The new version of the item
    :rtype: nailgun.entities.item
    """
    executed = False
    response = None
    while not executed:
      try:
        response = getattr(item, action)(**kwargs)
        log.debug(f"Response: {response}")
        executed = True
      except HTTPError as err:
        if action == "create" and err.response.status_code == 422:
          self.log_item(action, item, "Item is already present, updating")
          log.debug(f"HTTPError returned: {err.response.status_code}"
                    f"{err.response._content}")
          executed = True
          return self.nailrun(item, "update")
        elif err.response.status_code == 500:
          if ("Required lock is already taken by other running tasks"
              in str(err.response._content)):
            m = re.match(r'.*/foreman_tasks/tasks/([a-z0-9\-]+)',
                         str(err.response._content))
            self.log_item(action, item, "Task locked")
            if m:
              task = self.get_task("id", m.group(1))
              log.warning(f"{self.entity} locked by task {task.id}: {task.label}"
                       f" Started {task.started_at}, State: {task.state}"
                       f" Result: {task.result}"
                       f" Progress: {round(float(task.progress) * 100, 2)}%")
              if task.state == "paused":
                log.error("Task is in paused state, skipping job")
                executed = True
              else:
                sleep(5)
            else:
              log.error(f"{self.entity} locked: {err.response._content}")
            pass
          elif ("foreman_tasks_sync_task_timeout"
                in str(err.response._content)):
            # We skip here because the item is going to be there a bit later
            log.error(f"Task timeout, skipping: {err.response._content}")
            executed = True
            pass
        else:
          log.error(f"Error running {action} on {self.entity}: "
                    f"{err.response.status_code}  {err.response._content}")
          log.debug(f"Item: {item.__dict__}")
          executed = True
        pass
      except entity_mixins.TaskTimedOutError as err:
        log.error("TaskTimedOutError raised")
        log.exception(err)
        return item
      except Exception as err:
        log.error(f"Unknown exception {err}: {item}")
        log.error(f"Unknown exception {err}: (dict) {item.__dict__}")
        log.exception(err)
        raise Exception
    if response:
      return response
    else:
      return item

  def get_task(self, key, value):
    """Returns a task based on key/value

    :param key: Key to search on
    :type key: str
    :param value: Value to look for
    :type value: str
    :return: Task entity
    :rtype: nailgun.entities.Task
    """
    from forge.entities.task import Tasks
    task = Tasks(self._cfg).get(value, key)
    return task

  def get_tasks(self, key, value):
    """Returns list of tasks based on key/value

    :param key: Key to search on
    :type key: str
    :param value: Value to look for
    :type value: str
    :return: Task entities
    :rtype: list, nailgun.entities.Task
    """

    from forge.entities.task import Tasks
    tasks = Tasks(self._cfg).search(None, ** {key: value})
    return tasks

  def block_by_running_tasks(self):
    """Blocking loop that checks for any running tasks.
    The loop breaks when there are no more running tasks.
    """
    tasks = ["running tasks"]
    while len(tasks):
      log.info("Looking if there's still running tasks...")
      tasks = self.get_tasks("state", "running")
      for task in tasks:
        log.warning(
          f"{task.id}: {task.label} Started {task.started_at}, "
          f"State: {task.state} "
          f"Result: {task.result} "
          f"Progress: {round(float(task.progress) * 100, 2)}%")
        if len(task.input):
          for k, v in task.input.items():
            try:
              log.info(f"{k}: {v['name']}")
            except (KeyError, TypeError):
              pass
      sleep(5)

  def create(self, item, attribute_converter={}):
    """Wraps around the create_or_update to build the config_keys
    that are passed to the create or update function.

    :param item: Entity item to work on
    :type item: nailgun.entities.item
    :param attribute_converter: will convert some attributes to classes' items
    This is used mostly when creating domains and subnets, defaults to {}
    :type attribute_converter: dict, optional
    :return: Then entity item created by the create_or_update() method
    :rtype: nailgun.entities.item
    """
    item.description = "Automatically generated by Forge for Satellite"
    # Some creation (ie domains and subnets) need to have access to other
    # classes like Org and Location for their creation.
    for att, class_name in attribute_converter.items():
      config_keys = getattr(item, att)
      log.debug(f"Config key {att} {config_keys} {class_name}")
      module = load_module(path.dirname(path.realpath(__file__)), att,
                class_name)
      setattr(item, att, list(map(lambda x: module(self._cfg, name=x).get_or_new(x),
                                             config_keys.split(','))))
    # CVFRs can't have desc
    for key in self._forbidden_keys:
      try:
        delattr(item, key)
      except AttributeError:
        pass
    return self.create_or_update(item)

  def create_or_update(self, item):
    """Search satelite for a copy of an item we're about to create.
    If the item is there, we update it with the new attributes, if not, we create it

    By default, we search by `name`, but that can be overriden with the
    `_search_key` attribute on the forged entity.

    :param item: Entity item to work on
    :type item: nailgun.entities.item
    :return: The entity item that was either created or updated
    :rtype: nailgun.entities.item
    """
    search_string = {}
    search_item = item
    if self._search_key:
      search_item = None
      search_string[self._search_key] = getattr(item, self._search_key)
    if hasattr(item, "product_id"):
      search_string["product_id"] = item.product_id
    items = self.search(search_item, **search_string)
    if len(items):
      if len(items) > 1:
        log.warning(f"Found more than one item matching {search_string}, "
                    "taking the first.")

      old_item = items[0]
      self.log_item("create", item, "Item is already present, updating")
      log.debug(f"Old item: {old_item.__dict__}")
      old_item.__dict__.update(item.__dict__)
      log.debug(f"Resulting item: {old_item.__dict__}")
      self.item = self.nailrun(old_item, "update")
    else:
      log.debug(f"No item found matching {search_string}")
      self.item = self.nailrun(item, "create")
    return self.item
