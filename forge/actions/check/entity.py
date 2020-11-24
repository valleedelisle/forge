from prettytable import PrettyTable

from forge.actions.base import Base
from forge.entities.repository_set import RepositorySets


class CustomEntity(Base):
  def __init__(self, cfg, repo_type=None, enabled=False, label=None):
    super().__init__(cfg)
    self.repos = RepositorySets(cfg, self.org)
    search_string = {"per_page": 10000}
    if repo_type:
      search_string["content_type"] = repo_type
    if label:
      search_string["label"] = label
    items = self.repos.search(**search_string)
    x = PrettyTable()
    x.field_names = ["Repo Label", "Name", "Product", "Repositories"]
    for r in items:
      if not enabled or len(r.repositories) > 0:
        x.add_row([r.label, r.name, r.product.id, r.repositories])
    print(x)
