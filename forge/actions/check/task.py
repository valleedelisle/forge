import pprint
import sys
import tempfile

from logzero import logger as log
from prettytable import PrettyTable

from forge.actions.base import Base
from forge.entities.task import Tasks


class Task(Base):
  """ Satellite product creation
  """
  def __init__(self, cfg):
    super().__init__(cfg)
    self.skip_tasks = []
    self.only_tasks = []
    self.tasks = Tasks(cfg)

  def get_by_id(self, id):
    log.debug(f"Searching for task {id}")
    tasks = self.tasks.search(id=id)
    self._show_tasks(tasks)

  def reset_pulp_task(self, task_id):
    tmp = tempfile.NamedTemporaryFile()

    task = """\
@world = ForemanTasks.dynflow.world
@persistence = @world.persistence

def reset_pulp_task(foreman_uuid)
  uuid = ForemanTasks::Task.find(foreman_uuid).external_id
  execution_plan = @persistence.load_execution_plan(uuid)
  raise 'execution plan #{execution_plan} is not paused' unless """ \
      """execution_plan.state == :paused
  active_steps = execution_plan.steps_in_state(:running, :suspended, :error)
  active_steps.each do |step|
    action = step.action(execution_plan)
    if action.output['pulp_tasks']
      # delete a record about previous pulp tasks
      action.output.delete('pulp_tasks')
      puts "updating execution plan #{uuid} step #{step.id} action #{action.id}"
      @persistence.save_action(execution_plan.id, action)
    end
  end
  puts "resuming execution plan #{execution_plan.id}"
  @world.execute(execution_plan.id)
end

reset_pulp_task('%FOREMAN_TASK_ID%')"""
    script = task.replace('%FOREMAN_TASK_ID%', task_id)
    log.debug(script)
    with open(tmp.name, 'w') as f:
      f.write(script)
    log.info(tmp.name)
    cmd = ["foreman-rake", tmp.name, "--trace"]
    if self.run(cmd, "reset-pulp-task"):
      self.checkout()

  def get_incompletes(self):
    log.debug("Searching for incomplete tasks")
    tasks = self.tasks.search(state="stopped", operator="not")
    self._show_tasks(tasks)

  def _show_tasks(self, tasks):
    pp = pprint.PrettyPrinter(indent=2, width=200)
    if len(tasks) == 0:
      log.warning("No task found")
      sys.exit(0)
    for task in tasks:
      x = PrettyTable()
      x.field_names = ["Key", "Value"]
      x.align["Key"] = "r"
      x.align["Value"] = "l"
      x.max_width["Value"] = 80
      if task:
        if len(tasks) == 1:
          log.debug(pp.pformat(task.__dict__))
        duration = self.get_duration(task.started_at, task.ended_at)
        x.add_row(["State", task.state])
        x.add_row(["Pending", task.pending])
        x.add_row(["Result", self.color_by_name(task.result, task.result)])
        x.add_row(["Started", task.started_at])
        x.add_row(["Ended", task.ended_at])
        x.add_row(["Action", task.humanized["action"]])
        x.add_row(["Output", task.humanized["output"]])
        x.add_row(["Errors", task.humanized["errors"]])
        x.add_row(["Duration", duration])
        x.add_row(["Task ID", task.id])
        x.add_row(["Progress", "%s%%" % round(float(task.progress) * 100, 2)])
        if task.label == "Actions::Katello::Repository::Sync":
          sync = task.input["sync_result"]
          x.add_row(["Product", task.input['product']['label']])
          x.add_row(["Repository", task.input['repository']['label']])
          x.add_row(["Content Changed", task.input["contents_changed"]])
          if "poll_attempts" in sync:
            x.add_row(["Poll Attempts", "%s / %s failed"
                       % (sync["poll_attempts"]["failed"],
                          sync["poll_attempts"]["total"])])
          if "pulp_tasks" in sync:
            for ptask in sync["pulp_tasks"]:
              x.add_row(["Pulp Task", ptask["task_id"]])
              x.add_row(["Started", ptask["start_time"]])
              x.add_row(["Ended", ptask["finish_time"]])
              x.add_row(["Error", ptask["error"]])
              x.add_row(["State", ptask["state"]])
              x.add_row(["Type", ptask["task_type"]])
      print(x)
