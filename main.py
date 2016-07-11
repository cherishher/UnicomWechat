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
import time
import json,urllib
from mod.schoolbus.handler import SchoolBusHandler



from tornado.options import define, options
define('port', default=7000, help='run on the given port', type=int)

class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r'/wechata/',WechatHandler),
            (r'/wechata/register/([\S]+)',BindHandler),
            (r'/wechatanh/',WechatHandlera),
            (r'/webchata/schoolbus',SchoolBusHandler)
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
            'tuling':self.tuling_message,
            'schedule':self.classtable,
            'recharge':self.recharge,
            'query':self.query,
            'wlan':self.wlan,
            'freeflow':self.freeflow,
            'calender':self.calender,
            'schoolbus':self.schoolbus
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
                            print 'key error'
                        self.finish()
                elif self.wx.msg_type == 'text':
                    self.tuling()
                    self.finish()

                else:
                    self.write(self.wx.response_text_msg(u'??'))
                    self.finish()
            except:
                with open('wechat_error.log','a+') as f:
                    f.write(time.strftime('%Y%m%d %H:%M:%S in [wechat]', time.localtime(time()))+'\n'+str(sys.exc_info()[0])+str(sys.exc_info()[1])+'\n\n')
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
        msg =  u'<a href="%s/allweixin">戳我快速领取通信卡！</a>' %CARD_URL
        self.write(self.wx.response_text_msg(msg))
    def tuling_message(self):
        msg = u'直接发送消息可进行调戏呦~'
        self.write(self.wx.response_text_msg(msg))

    def tuling(self):
        try:
            msg = u''
            msg = self.tuling_response(self.wx.raw_content,self.wx.openid)
            self.write(self.wx.response_text_msg(msg))
        except Exception,e:
            msg = u'哦no！人家被玩坏了,等会再调戏人家好不好啊~'
            self.write(self.wx.response_text_msg(msg))

    def classtable(self):
        try:
            user = self.db.query(Cardnum).filter(Cardnum.openid == self.wx.openid).one()
            print user
            msg = u""
            result = self.get_class(user.cardnum)
            for i in range(len(result)):
                msg += result[i][0]+"\n"
                msg += result[i][1]+"\n"
                msg += result[i][2]+"\n"
                msg += '\n'
            self.write(self.wx.response_text_msg(msg))
        except NoResultFound:
            msg = u'<a href="%s/register/%s">您尚未进行绑定，点我绑定哦！</a>'%(LOCAL,self.wx.openid)
            self.write(self.wx.response_text_msg(msg))
        except Exception,e:
            msg = u'没有查到你的课表哎，你今天不会是没有课吧~'
            self.write(self.wx.response_text_msg(msg))
    # def openid_to_cardnum(self,openid):
    #     user = self.db.query(Cardnum).filter(Cardnum.openid == openid).one()
    #     return user.cardnum

    def tuling_response(self,info,openid):
        client = HTTPClient()
        data = {
            'info':info.encode('utf-8'),
            'cardnum':openid
        }
        request = HTTPRequest(
            url = tuling_url,
            method = 'POST',
            body = urllib.urlencode(data)
        )
        response = client.fetch(request)
        content = json.loads(response.body)
        message = json.loads(content['retinfo'])['text']
        return message

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
        week = str(time.strftime("%w"))
        todayclass = content['content'][week]
        return todayclass

    def recharge(self):
        msg =  u'<a href="%s/allweixin">戳我快速充值！</a>' %dnrecharge_url
        self.write(self.wx.response_text_msg(msg))

    def query(self):
        msg =  u'请关注WO江苏微信公众号获取'
        self.write(self.wx.response_text_msg(msg))

    def wlan(self):
        msg =  u'<a href="%s/allweixin">wlan服务！</a>' %dnwlan_url
        self.write(self.wx.response_text_msg(msg))

    def freeflow(self):
        msg =  u'<a href="%s/allweixin">戳我领取新生专属免费流量！</a>' %dnfreeflow_url
        self.write(self.wx.response_text_msg(msg))

    def schoolbus(self):
        msg = self.getschoolbus()
        self.write(self.wx.response_text_msg(msg))

    def calender(self):
        msg =  u'<a href="%s/allweixin">戳我查看校历！</a>' %dncalender_url
        self.write(self.wx.response_text_msg(msg))

    def getschoolbus(self):
        client = HTTPClient()
        request = HTTPRequest(
            url = schoolbus_url,
            method = 'GET'
        )
        response = client.fetch(request)
        content = json.loads(response.body)
        message = json.loads(content['holiday'])
        return message


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



class WechatHandlera(tornado.web.RequestHandler):

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
            'tuling':self.tuling_message,
            'signup':self.signup,
            'vote':self.vote,
            'upload':self.upload,
            'recharge':self.recharge,
            'query':self.query,
            'price':self.price,
            'freeflow':self.freeflow
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
                        self.write(self.wx.response_text_msg(ResponseContentnh))
                        self.finish()
                    elif self.wx.event == 'unsubscribe':
                        self.write(self.wx.response_text_msg(u'谢谢您的关注'))
                        self.finish()
                    elif self.wx.event == 'CLICK':
                        try:
                            self.unitsmap[self.wx.event_key]()
                        except KeyError:
                            print 'key error'
                        self.finish()
                elif self.wx.msg_type == 'text':
                    self.tuling()
                    self.finish()

                else:
                    self.write(self.wx.response_text_msg(u'??'))
                    self.finish()
            except:
                with open('wechat_error.log','a+') as f:
                    f.write(time.strftime('%Y%m%d %H:%M:%S in [wechat]', time.localtime(time()))+'\n'+str(sys.exc_info()[0])+str(sys.exc_info()[1])+'\n\n')
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
        msg =  u'<a href="%s/allweixin">戳我快速领取通信卡！</a>' %NHCARD_URL
        self.write(self.wx.response_text_msg(msg))
    def tuling_message(self):
        msg = u'直接发送消息可进行调戏呦~'
        self.write(self.wx.response_text_msg(msg))

    def tuling(self):
        try:
            msg = u''
            msg = self.tuling_response(self.wx.raw_content,self.wx.openid)
            self.write(self.wx.response_text_msg(msg))
        except Exception,e:
            msg = u'哦no！人家被玩坏了,等会再调戏人家好不好啊~'
            self.write(self.wx.response_text_msg(msg))

    def tuling_response(self,info,openid):
        client = HTTPClient()
        data = {
            'info':info.encode('urf-8'),
            'cardnum':openid
        }
        request = HTTPRequest(
            url = tuling_url,
            method = 'POST',
            body = urllib.urlencode(data)
        )
        response = client.fetch(request)
        content = json.loads(response.body)
        message = json.loads(content['retinfo'])['text']
        return message

    def signup(self):
        signupurl  = 'http://unicom.maomengtv.com/unicom/yinc/toapply?from=singlemessage&isappinstalled=0'
        msg =  u'<a href="%s/allweixin">音超报名</a>' % signupurl
        self.write(self.wx.response_text_msg(msg))

    def vote(self):
        voteurl = 'http://unicom.maomengtv.com/unicom/yinc/subject?from=singlemessage&isappinstalled=0'
        msg =  u'<a href="%s/allweixin">音超投票</a>' % voteurl
        self.write(self.wx.response_text_msg(msg))

    def upload(self):
        uploadurl = 'http://unicom.maomengtv.com/unicom/yinc/down?from=singlemessage&isappinstalled=0'
        msg =  u'<a href="%s/allweixin">音超视频上传</a>' % uploadurl
        self.write(self.wx.response_text_msg(msg))

    def recharge(self):
        msg =  u'<a href="%s/allweixin">戳我快速充值！</a>' %nhrecharge_url
        self.write(self.wx.response_text_msg(msg))

    def query(self):
        msg =  u'请关注wo江苏微信公众号后查询'
        self.write(self.wx.response_text_msg(msg))

    def freeflow(self):
        msg =  u'<a href="%s/allweixin">戳我领取新生专属免费流量！</a>' %nhfreeflow_url
        self.write(self.wx.response_text_msg(msg))

    def price(self):
        msg =  u'<a href="%s/allweixin">戳我参与抽奖！</a>' %nhprice_url
        self.write(self.wx.response_text_msg(msg))

    def schoolbus(self):
        msg=u'该查询不久后开通'
        self.write(self.wx.response_text_msg(msg))


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
