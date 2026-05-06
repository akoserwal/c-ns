#!/usr/bin/env python3.12

import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database address/settings -- resolve relative to this file's location
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
URL = f"sqlite:///{os.path.join(_BASE_DIR, '..', '..', 'movielook.db')}"

# Database engine
engine = create_engine(URL, connect_args={"check_same_thread": False})

# Session creator
Connect = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db():
    """Generate database session"""
    db = Connect()
    try:
        yield db
    finally:
        db.close()
