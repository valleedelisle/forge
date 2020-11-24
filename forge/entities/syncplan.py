from datetime import date, datetime, time, timedelta

from forge.entities.base import Base


class SyncPlans(Base):
  days = ['monday', 'tuesday', 'wednesday',
          'thursday', 'friday', 'saturday',
          'sunday']

  def __init__(self, cfg, org):
    self.entity = "SyncPlan"
    super().__init__(cfg, org)

  def next_day(self, weekday, hour):
    now = datetime.combine(date.today(), time(hour))
    day_shift = (self.days.index(weekday) - now.weekday()) % 7
    return now + timedelta(days=day_shift)

  def get_by_interval(self, interval):
    self.get_all()
    return list(filter(lambda x: x.interval == interval, self.items))

  def get_plan_map(self, interval):
    return list(map(
      lambda x: x.id,
      SyncPlans(self._cfg, self.org).get_by_interval(interval)))

  def create_all(self):
    for section in self._cfg.config:
      if section.startswith("syncplans"):
        name = "-".join(section.split("-")[1:])
        interval = self._cfg.config[section].get("interval")
        if interval == "daily":
          for i in range(1, 6):
            item = self.new_item()
            item.name = f"{name}-{i}"
            item.interval = interval
            item.sync_date = datetime.combine(
              date.today() + timedelta(days=1), time(i))
            self.create(item)
        else:
          item = self.new_item()
          item.name = name
          item.interval = interval
          item.sync_date = self.next_day(self._cfg.config[section]
                                                   .get("day"), 0)
          self.create(item)
