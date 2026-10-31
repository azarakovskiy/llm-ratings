"""UI-independent advice state over one already loaded Dataset.

The shared query owns selection and advice policy. Transitions retain unrelated
choices and discard row/detail keys when their result set changes.
"""

from . import render


class Session:
    """Active choices and explicit evidence requests, without terminal state."""

    def __init__(self, ds, roles, role_name=None):
        if not roles:
            raise ValueError("session requires at least one role")
        self.ds = ds
        self.roles = roles
        self.role = (roles[0] if role_name is None else
                     next((r for r in roles if r["name"] == role_name), None))
        if self.role is None:
            raise ValueError(f"unknown role: {role_name!r}")
        self.objective_override = None
        self.min_grade = None
        self.provider = None
        self.view = "table"
        self.selected_key = None
        self.detail_key = None

    @property
    def objective(self):
        return self.objective_override or self.role["objective"]

    @staticmethod
    def _record(result, key):
        if key is None:
            return None
        return next((row for group in ("rows", "excluded", "unranked")
                     for row in result[group] if row["key"] == key), None)

    def query(self):
        result = render.query(self.ds, self.role,
                              objective=self.objective_override,
                              min_grade=self.min_grade,
                              provider=self.provider, view=self.view)
        result["selected"] = self._record(result, self.selected_key)
        result["details"] = result["detail_targets"].get(self.detail_key)
        return result

    def _changed(self):
        self.selected_key = None
        self.detail_key = None
        return self.query()

    def set_role(self, name):
        role = next((r for r in self.roles if r["name"] == name), None)
        if role is None:
            raise ValueError(f"unknown role: {name!r}")
        self.role = role
        self.objective_override = None
        return self._changed()

    def set_objective(self, objective):
        if objective is not None and objective not in render.OBJECTIVES:
            raise ValueError(f"unknown objective: {objective!r}")
        self.objective_override = objective
        return self._changed()

    def set_min_grade(self, min_grade):
        if min_grade is not None and (
                type(min_grade) is not int or min_grade not in render.CAPABILITY_FILTERS):
            raise ValueError(f"unknown capability display filter: {min_grade!r}")
        self.min_grade = min_grade
        return self._changed()

    def set_provider(self, name):
        if name is not None and (
                not isinstance(name, str)
                or name not in render.PROVIDER_SHORTCUTS
                and name not in render.creators(self.ds)):
            raise ValueError(f"unknown provider: {name!r}")
        self.provider = name
        return self._changed()

    def set_view(self, view):
        if not isinstance(view, str) or view not in render.VIEW_LABEL:
            raise ValueError(f"unknown view: {view!r}")
        self.view = view
        return self._changed()

    def select_model(self, key):
        """Move passive selection without opening or closing requested details."""
        result = self.query()
        selected = self._record(result, key)
        if key is not None and (not isinstance(key, str) or selected is None):
            raise ValueError(f"model is not in the current result: {key!r}")
        self.selected_key = key
        result["selected"] = selected
        return result

    def request_details(self, key):
        result = self.query()
        if not isinstance(key, str) or key not in result["detail_targets"]:
            raise ValueError(f"model has no details target in the current view: {key!r}")
        details = result["detail_targets"][key]
        self.detail_key = key
        result["details"] = details
        return result

    def close_details(self):
        self.detail_key = None
        return self.query()

    def recover(self, action):
        """Apply only the named choice; never relax another active constraint."""
        if action == "all_providers":
            return self.set_provider(None)
        if action == "clear_capability":
            return self.set_min_grade(None)
        if action == "highest_capability":
            return self.set_objective("cap")
        if action == "role_default":
            return self.set_objective(None)
        raise ValueError(f"unknown recovery action: {action!r}")
