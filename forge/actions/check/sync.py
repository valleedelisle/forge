from prettytable import PrettyTable

from forge.actions.base import Base
from forge.entities.organization import Org
from forge.entities.repository import Repositories


class Sync(Base):
  """ Satellite product creation
  """
  def __init__(self, cfg):
    super().__init__(cfg)
    self.org = Org(cfg, name=self._cfg.satellite["default_org"])
    self.repos = Repositories(cfg, self.org)
    self.repos.get_all()
    x = PrettyTable()
    x.field_names = ["Repo Label", "Product Label", "Sync State",
                     "Result", "Time", "Duration", "Task ID"]
    for r in self.repos.items:
      product = r.product.read()
      task = r.last_sync.read()
      if not task:
        continue
      duration = self.get_duration(task.started_at, task.ended_at)
      fields = [r.label, product.label, task.state, task.result, task.started_at,
                duration, task.id]
      row = []
      for field in fields:
        row.append(self.color_by_name(task.result, field))
      x.add_row(row)
    print(x)
