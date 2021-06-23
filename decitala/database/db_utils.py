from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

def get_session(db_path, echo=False):
	engine = create_engine(f"sqlite:////{db_path}", echo=echo)
	Base.metadata.create_all(engine)

	Session = sessionmaker(bind=engine)
	session = Session()
	return session