from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

def get_session(db_path, base, echo=False):
	engine = create_engine(f"sqlite:////{db_path}", echo=echo)
	base.metadata.create_all(engine)

	Session = sessionmaker(bind=engine)
	session = Session()
	return session


FRAGMENT_BASE = declarative_base()
TRANSCRIPTION_BASE = declarative_base()