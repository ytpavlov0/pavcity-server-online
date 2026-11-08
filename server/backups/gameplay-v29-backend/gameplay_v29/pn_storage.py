"""One connection per authenticated request; nested contexts use savepoints.

Connections close at request completion. No cross-request money/role cache.
Outside a request the caller keeps the previous short-lived DB semantics.
"""
from contextlib import contextmanager
import threading
import online_engine as engine
LOCAL = threading.local()

@contextmanager
def request():
    if getattr(LOCAL, 'db', None) is not None:
        yield
        return
    db = engine.get_db()
    LOCAL.db = db
    LOCAL.depth = 0
    LOCAL.serial = 0
    try:
        yield
    finally:
        try:
            db.close()
        finally:
            LOCAL.db = None
            LOCAL.depth = 0

@contextmanager
def database():
    db = getattr(LOCAL, 'db', None)
    if db is None:
        with request():
            with database() as current:
                yield current
        return
    depth = LOCAL.depth
    LOCAL.depth += 1
    LOCAL.serial += 1
    name = 'pav_sp_' + str(LOCAL.serial)
    try:
        if depth:
            db.execute('SAVEPOINT ' + name)
            try:
                yield db
            except BaseException:
                db.execute('ROLLBACK TO ' + name)
                db.execute('RELEASE ' + name)
                raise
            else:
                db.execute('RELEASE ' + name)
        else:
            with db:
                yield db
    finally:
        LOCAL.depth -= 1
