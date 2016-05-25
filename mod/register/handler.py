# -*- coding: utf-8 -*-
# @Date    : 2016/5/25  19:54
# @Author  : 490949611@qq.com
# -*- coding: utf-8 -*-
# @Date    : 2016-05-19 17:27
# @Author  : max

from BeautifulSoup import BeautifulSoup
from config import *
from tornado.httpclient import HTTPRequest, AsyncHTTPClient
from collections import OrderedDict
from sqlalchemy.orm.exc import NoResultFound
from time import time
import tornado.web
import tornado.gen
from ..db.cardnum import Cardnum
import requests
import urllib
import json
import re

class BindHandler(tornado.web.RequestHandler):

    def get(self,openid):
        self.render('bangding.html',openid = openid)

    @property
    def db(self):
        return self.application.db
    def on_finish(self):
        self.db.close()
    @tornado.web.asynchronous
    @tornado.gen.engine
    def post(self,openid):
		flag = True
		cardnum = self.get_argument('cardnum',default=None)
		user = self.db.Query(Cardnum).filter(Cardnum.cardnum == cardnum).one()
		if not openid:
			self.write("accesss failed")
			flag = False
		elif not cardnum:
			self.write("请填入完整信息哦！")
			flag = False
		elif user:
			self.write("该用户已经绑定咯")
			flag = False
		if flag:
			new_cardnum = Cardnum(cardnum = cardnum,openid = openid)
			self.db.add(new_cardnum)
			self.db.commit()
			self.write('绑定成功！')
		self.finish()
