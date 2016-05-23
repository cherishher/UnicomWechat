# -*- coding: utf-8 -*-
# @Date    : 2016-05-19 17:47
# @Author  : max

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from db import engine

Base = declarative_base()

class Cardnum(Base):
	__tablename__ = 'cardnum'
	key = Column(Integer,primary_key=True)
	cardnum = Column(String(1024),nullable=False)

if __name__ == '__main__':
	Base.metadata.create_all(engine)
