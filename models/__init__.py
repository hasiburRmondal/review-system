# /models/__init__.py
from flask_sqlalchemy import SQLAlchemy

# Create the SQLAlchemy object
db = SQLAlchemy()

# Import the models to ensure they are registered with SQLAlchemy
from .user import User, UserMeta
from .review import Review
from .ticket import Ticket

# You can also add other model imports here if you create more models
