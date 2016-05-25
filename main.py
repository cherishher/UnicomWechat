#!/usr/bin/python
# -*- coding: utf-8 -*-
#@date  :2015-3-22

from config import *
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from tornado.httpclient import HTTPRequest, AsyncHTTPClient,HTTPClient
from mod.db.cardnum import Cardnum
from mod.register.handler import BindHandler
from mod.db.db import engine
import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.options
import tornado.gen
import os, sys
import check
import random
import json,urllib
from time import localtime, strftime, time



from tornado.options import define, options
define('port', default=7000, help='run on the given port', type=int)

class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r'/wechata/',WechatHandler),
            (r'/wechata/register/([\S]+)',BindHandler)
            ]
        settings = dict(
            cookie_secret="7CA71A57B571B5AEAC5E64C6042415DE",
            template_path=os.path.join(os.path.dirname(__file__), 'templates'),
            static_path=os.path.join(os.path.dirname(__file__), 'static'),
            # static_url_prefix = os.path.join(os.path.dirname(__file__), '/images/'),
            debug=True
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        self.db = scoped_session(sessionmaker(bind=engine,
                                              autocommit=False, autoflush=True,
                                              expire_on_commit=False))


class WechatHandler(tornado.web.RequestHandler):

    @property
    def client(self):
        client = AsyncHTTPClient()

    @property
    def db(self):
        return self.application.db

    @property
    def unitsmap(self):
        return {
            'nothing':self.nothing,
            'unicomCard':self.unicomcard,
            'tuling':self.tuling,
            'schedule':self.classtable
        }
    def on_finish(self):
        self.db.close()

    def get(self):
        self.wx = check.Message(token='Unicom')
        if self.wx.check_signature(self.get_argument('signature', default=''),
                                   self.get_argument('timestamp', default=''),
                                   self.get_argument('nonce', default='')
                                   ):
            self.write(self.get_argument('echostr'))
        else:
            self.write('access verification fail')

    @tornado.web.asynchronous
    def post(self):
        self.wx = check.Message(token='Unicom')
        if self.wx.check_signature(self.get_argument('signature', default=''),
                                   self.get_argument('timestamp', default=''),
                                   self.get_argument('nonce', default='')
                                   ):
            self.wx.parse_msg(self.request.body)
            try:
                if self.wx.msg_type == 'event' :
                    if self.wx.event =='subscribe':
                        self.write(self.wx.response_text_msg(ResponseContent))
                        self.finish()
                    elif self.wx.event == 'unsubscribe':
                        self.write(self.wx.response_text_msg(u'谢谢您的关注'))
                        self.finish()
                    elif self.wx.event == 'CLICK':
                        try:
                            self.unitsmap[self.wx.event_key]()
                        except KeyError:
                            pass
                        self.finish()
                elif self.wx.msg_type == 'text':

                    self.finish()

                else:
                    self.write(self.wx.response_text_msg(u'??'))
                    self.finish()
            except:
                with open('wechat_error.log','a+') as f:
                    f.write(strftime('%Y%m%d %H:%M:%S in [wechat]', localtime(time()))+'\n'+str(sys.exc_info()[0])+str(sys.exc_info()[1])+'\n\n')
                self.write(self.wx.response_text_msg(u'出了点问题T_T,稍后再试吧~'))
                self.finish()
        else:
            self.write('message processing fail')
            self.finish()
    
    def nothing(self):
        # msg = u'您好! 您可以直接回复“提问+您的问题”我们将为您解答，答疑时间为周一至周五09：00-17：00. 东南大学学生事务服务中心联系方式：025-52090282，九龙湖校区大活524。'
        msg = u' '
        # self.write(self.wx.response_text_msg(msg))
    def unicomcard(self):
        msg =  u'<a href="%s/allweixin">戳我快速办理手机卡！</a>' %CARD_URL
        self.write(self.wx.response_text_msg(msg))
    def tuling(self):
        try:
            user = self.db.query(Cardnum).filter(Cardnum.openid == self.wx.openid).one()
            msg = tuling_url(self.wx.content,self.wx.openid)
            self.write(self.wx.response_text_msg(msg))
        except NoResultFound:
            msg = u'<a href="%s/register/%s">您尚未进行绑定，点我绑定哦！</a>'%(LOCAL,self.wx.openid)
            self.write(self.wx.response_text_msg(msg))
    def classtable(self):
        try:
            user = self.db.query(Cardnum).filter(Cardnum.openid == self.wx.openid).one()
            msg = self.get_class(user.cardnum)
            self.write(self.wx.response_text_msg(msg))
        except NoResultFound:
            msg = u'<a href="%s/register/%s">您尚未进行绑定，点我绑定哦！</a>'%(LOCAL,self.wx.openid)
            self.write(self.wx.response_text_msg(msg))

    # def openid_to_cardnum(self,openid):
    #     user = self.db.query(Cardnum).filter(Cardnum.openid == openid).one()
    #     return user.cardnum

    def tuling_response(self,info,openid):
        client = HTTPClient()
        data = {
            'info':info,
            'cardnum':openid
        }
        request = HTTPRequest(
            url = tuling_url,
            method = 'POST',
            body = urllib.urlencode(data)
        )
        response = client.fetch(request)
        content = json.loads(response.body)
        return content

    def get_class(self,cardnum):
        # cardnum = self.openid_to_cardnum(openid)
        client = HTTPClient()
        data = {
            'term':TERM,
            'cardnum':cardnum
        }
        request = HTTPRequest(
            url = class_url,
            method = 'POST',
            body = urllib.urlencode(data)
        )
        response = client.fetch(request)
        content = json.loads(response.body)
        return content
    # def change_pwd(self):
    #     try:
    #         teacher = self.db.query(Teacher).filter(Teacher.openid == self.wx.openid).one()
    #         msg = u'尊敬的%s,您好！<a href="%s/update/%s">点击修改密码</a>' %(teacher.name,URL,self.wx.openid)
    #         self.write(self.wx.response_text_msg(msg))
    #     except NoResultFound:
    #         msg = u'<a href="%s/Tregister/%s">您尚未进行登录注册，点我进行注册登录哦</a>' % (URL, self.wx.openid)
    #         self.write(self.wx.response_text_msg(msg))
    # def delete(self):
    #     try:
    #         teacher = self.db.query(Teacher).filter(Teacher.openid == self.wx.openid).one()
    #         teacher.openid = None
    #         msg = u'尊敬的%s,您好！注销成功' % teacher.name
    #         self.write(self.wx.response_text_msg(msg))
    #     except NoResultFound:
    #         msg = u'<a href="%s/Tregister/%s">您尚未进行登录注册，点我进行注册登录哦</a>' % (URL, self.wx.openid)
    #         self.write(self.wx.response_text_msg(msg))
    # def register_infor(self):
    #     try:
    #         teacher = self.db.query(Teacher).filter(Teacher.openid == self.wx.openid).one()
    #         msg = u'尊敬的%s，您好！您的房间号为:%s' % (teacher.name,teacher.room)
    #         self.write(self.wx.response_text_msg(msg))
    #     except NoResultFound:
    #         msg = u'<a href="%s/Tregister/%s">您尚未进行登录注册，点我进行注册登录哦</a>' % (URL, self.wx.openid)
    #         self.write(self.wx.response_text_msg(msg))
    # def party_arrangement(self):
    #     try:
    #         teacher = self.db.query(Teacher).filter(Teacher.openid == self.wx.openid).one()
    #         msg = u'尊敬的%s，您好！<a href="%s">点击查看详细会议安排</a>' % (teacher.name,party_url)
    #         self.write(self.wx.response_text_msg(msg))
    #     except NoResultFound:
    #         msg = u'<a href="%s/Tregister/%s">您尚未进行登录注册，点我进行注册登录哦</a>' % (URL, self.wx.openid)
    #         self.write(self.wx.response_text_msg(msg))
    # def download(self):
    #     try:
    #         teacher = self.db.query(Teacher).filter(Teacher.openid == self.wx.openid).one()
    #         msg = u'尊敬的%s，您好，<a href="%s/fileList">请点击下载资料</a>' % (teacher.name,URL)
    #         self.write(self.wx.response_text_msg(msg))
    #     except NoResultFound:
    #         msg = u'<a href="%s/Tregister/%s">您尚未进行登录注册，点我进行注册登录哦</a>' % (URL, self.wx.openid)
    #         self.write(self.wx.response_text_msg(msg))
    # def communicate(self):
    #     try:
    #         teacher = self.db.query(Teacher).filter(Teacher.openid == self.wx.openid).one()
    #         msg = u'尊敬的%s，您好，<a href="%s">请点击加入交流群</a>' % (teacher.name,com_url)
    #         self.write(self.wx.response_text_msg(msg))
    #     except NoResultFound:
    #         msg = u'<a href="%s/Tregister/%s">您尚未进行登录注册，点我进行注册登录哦</a>' % (URL, self.wx.openid)
    #         self.write(self.wx.response_text_msg(msg))
    


if __name__ == '__main__':
    tornado.options.parse_command_line()
    Application().listen(options.port)
    tornado.ioloop.IOLoop.instance().start()