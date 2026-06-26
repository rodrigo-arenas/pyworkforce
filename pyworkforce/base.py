"""Shared base classes for pyworkforce estimators.

The :class:`BaseWorkforce` mixin gives every solver a consistent,
scikit-learn-like ``repr`` and a ``get_params`` method. This makes objects
easy to inspect interactively and keeps the public API predictable across the
queuing, scheduling and rostering modules.
"""

import inspect


class BaseWorkforce:
    """Mixin providing ``get_params`` and a readable ``__repr__``.

    Subclasses only need to store each ``__init__`` argument as an attribute of
    the same name (the scikit-learn convention). Parameters captured through
    ``*args``/``**kwargs`` are ignored.
    """

    @classmethod
    def _param_names(cls):
        """Return the ordered list of explicit ``__init__`` parameter names."""
        init = cls.__init__
        if init is object.__init__:
            return []
        signature = inspect.signature(init)
        return [
            name
            for name, parameter in signature.parameters.items()
            if name != "self"
            and parameter.kind not in (parameter.VAR_KEYWORD, parameter.VAR_POSITIONAL)
        ]

    def get_params(self):
        """Return the estimator parameters as a ``{name: value}`` dictionary.

        Returns
        -------
        dict
            Mapping of each ``__init__`` parameter name to its current value.
        """
        return {name: getattr(self, name, None) for name in self._param_names()}

    def __repr__(self):
        params = self.get_params()
        formatted = ", ".join(f"{name}={value!r}" for name, value in params.items())
        return f"{type(self).__name__}({formatted})"
