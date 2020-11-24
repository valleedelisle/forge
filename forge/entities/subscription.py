from forge.entities.base import Base
from nailgun.entity_mixins import MissingValueError


class Subscriptions(Base):
  def __init__(self, cfg, **kwargs):
    self.entity = "Subscription"
    super().__init__(cfg, **kwargs)

  def get_all_subs(self):
    self.get_all()
    sub_list = []
    for i in self.items:
      try:
        sub = i.subscription.read()
      # The insights repos doesn't contain a product_provided field
      # so it breaks here
      except MissingValueError:
        continue
      sub_list.append(sub)
    self.sub_items = sub_list
    return sub_list

  def get_subs_for_product(self, product):
    return list(filter(lambda x: product.id in map(lambda y: y.id,
      x.provided_product), self.sub_items))
