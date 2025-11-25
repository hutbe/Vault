from sqlalchemy import Column, Integer, BIGINT, String, Text, DateTime, Numeric, Boolean, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20), nullable=False)
    alias = Column(String(20))
    email = Column(String(20))
    gender = Column(Integer, default=0)
    phoneNumber = Column(String(20))
    introduction = Column(Text)
    createDate = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'alias': self.alias,
            'email': self.email,
            'gender': self.gender,
            'phoneNumber': self.phoneNumber,
            'introduction': self.introduction,
            'createDate': self.createDate.isoformat() if self.createDate else None
        }
