#!/usr/bin/python
# -*- coding: utf-8 -*-
import hashlib
import time
import xml.etree.ElementTree as ET

class Message(object):

    TEXT_MSG = u"""
<xml>
<ToUserName><![CDATA[{to_user_name}]]></ToUserName>
<FromUserName><![CDATA[{from_user_name}]]></FromUserName>
<CreateTime>{create_time}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{content}]]></Content>
</xml>
"""
    PIC_MSG = u"""
<xml>
<ToUserName><![CDATA[{to_user_name}]]></ToUserName>
<FromUserName><![CDATA[{from_user_name}]]></FromUserName>
<CreateTime>{create_time}</CreateTime>
<MsgType><![CDATA[news]]></MsgType>
<ArticleCount>1</ArticleCount>
<Articles>
<item>
<Title><![CDATA[{title}]]></Title>
<Description><![CDATA[{description}]]></Description>
<PicUrl><![CDATA[{picurl}]]></PicUrl>
<Url><![CDATA[{url}]]></Url>
</item>
</Articles>
</xml>
"""
    def __init__(self, token):
        self.token = token
        self.msg = {}

        
    def check_signature(self, signature, timestamp, nonce):
        tmplist = [self.token, timestamp, nonce]
        tmplist.sort()
        tmpstr = ''.join(tmplist)
        hashstr = hashlib.sha1(tmpstr).hexdigest()

        if hashstr == signature:
            return True
        else:
            return False

    def parse_msg(self, msg):
        root = ET.fromstring(msg)
        for child in root:
            self.msg[child.tag] = child.text
        return self.msg

    @property
    def msg_type(self):
        return self.msg.get('MsgType', None)

    @property
    def event(self):
        return self.msg.get('Event', None)

    @property
    def event_key(self):
        return self.msg.get('EventKey', None)

    @property
    def raw_content(self):
        return self.msg.get('Content', None)

    @property
    def content(self):
        content = self.msg.get('Content',None)
        if u'办卡' in content:
            return 'unicomCard'
        elif content==u'调戏' :
            return 'tuling'
        elif content == u'课表' :
            return 'schedule'

    @property
    def openid(self):
        return self.msg.get('FromUserName', None)
    def response_text_msg(self, content):
        return self.TEXT_MSG.format(to_user_name=self.msg['FromUserName'],
                                    from_user_name=self.msg['ToUserName'],
                                    create_time=str(int(time.time())),
                                    content=content)

    def response_pic_msg(self, title, pic_url, content, url):
        return self.PIC_MSG.format(to_user_name=self.msg['FromUserName'],
                                    from_user_name=self.msg['ToUserName'],
                                    create_time=str(int(time.time())),
                                    title=title,
                                    description=content,
                                    picurl=pic_url,
                                    url=url)