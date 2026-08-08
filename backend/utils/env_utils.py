"""Environment resolution helpers shared across backend modules."""

import os

from backend.constants import VALID_APP_ENVS


def get_required_app_env() -> str:
    """Return APP_ENV, requiring it to be explicitly one of VALID_APP_ENVS.

    Fails closed rather than silently defaulting to "dev", which would
    otherwise expose /docs and /redoc and disable secure session cookies
    in any deployment where APP_ENV is accidentally left unset.

    Raises:
        RuntimeError: If APP_ENV is unset or not a recognised environment.
    """
    app_env = os.getenv("APP_ENV")
    if app_env not in VALID_APP_ENVS:
        raise RuntimeError(
            f"APP_ENV must be explicitly set to one of {VALID_APP_ENVS}, got {app_env!r}"
        )
    return app_env
