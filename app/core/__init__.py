"""Core package exports.

Individual sub-modules are imported lazily to avoid dragging in the DB engine
(and asyncpg) at package-import time.  Import directly from the sub-modules
when you need them:

    from app.core.security import create_access_token
    from app.core.dependencies import get_current_user, require_roles
    from app.core.logging import get_logger
"""
