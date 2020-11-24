from forge.entities.base import Base


class ContentViewFilterRules(Base):
  """Forged ContentViewFilterRules object.
  Matches nailgun.entity.ContentViewFilterRule

  :param Base: forge.entities.Base
  :type Base: BaseClass
  :return: List of ContentViewFilterRule entities
  :rtype: list
  """
  def __init__(self, cfg, **kwargs):
    """Class initialization

    :param cfg: Configuration object
    :type cfg: forge.config
    """
    self.entity = "ContentViewFilterRule"
    self.content_view_filter = kwargs["content_view_filter"]
    self._pass_to_new = ["content_view_filter"]
    self._search_key = None
    self._forbidden_keys = ["description"]
    super().__init__(cfg, pass_to_new=["content_view_filter"], **kwargs)
