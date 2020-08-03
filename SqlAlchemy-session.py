from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session

engine = create_engine("mysql+pymysql://root:1234@127.0.0.1:3306", max_overflow=0)
Session = sessionmaker(bind=engine)
session = scoped_session(Session)

session.add()
session.commit()
