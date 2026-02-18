from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask import g

SessionLocal = None

def init_engine(database_url):
    global SessionLocal
    engine = create_engine(database_url, future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return engine

@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def get_session():
    if 'db_session' not in g:
        g.db_session = SessionLocal()
    return g.db_session

def close_session(e=None):
    session = g.pop('db_session', None)
    if session is not None:
        if e is None:
            session.commit()
        else:
            session.rollback()
        session.close()
