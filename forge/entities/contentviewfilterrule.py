from forge.entities.base import Base


class ContentViewFilterRules(Base):
  """ Satellite Content-views creation
  This is where we generate the content-views
  """
  def __init__(self, cfg, **kwargs):
    self.entity = "ContentViewFilterRule"
    self.content_view_filter = kwargs["content_view_filter"]
    self._pass_to_new = ["content_view_filter"]
    self._search_key = None
    self._forbidden_keys = ["description"]
    super().__init__(cfg, pass_to_new=["content_view_filter"], **kwargs)
