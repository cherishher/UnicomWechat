# -*- coding: utf-8 -*-
# @Date    : 2016/7/8  22:58
# @Author  : 490949611@qq.com

import tornado.web
from sqlalchemy.orm.exc import NoResultFound
import json, base64

class SchoolBusHandler(tornado.web.RequestHandler):

    @property
    def db(self):
        return self.application.db

    def get(self):
        self.return_holiday()

    def return_holiday(self):
        bus_json = {
            "holiday":{
                "出九龙湖":[
                    { "time":"8:00-9:30", "bus":"每 30min 一班"},
                    { "time":"9:30-11:30", "bus":"每 1h 一班"},
                    { "time":"11:30-13:00", "bus":"每 30min 一班"},
                    { "time":"13:30-17:00", "bus":"每 1h 一班(最后一班为17:00)"},
                    { "time":"17:00-19:00", "bus":"每 30min 一班"},
                    { "time":"19:00-22:00", "bus":"每 1h 一班"}
                ],
                "进九龙湖":[
                    { "time":"8:00-9:30", "bus":"每 30min 一班"},
                    { "time":"9:30-11:30", "bus":"每 1h 一班"},
                    { "time":"11:30-13:00", "bus":"每 30min 一班"},
                    { "time":"13:30-17:00", "bus":"每 1h 一班(最后一班为17:00)"},
                    { "time":"17:00-19:00", "bus":"每 30min 一班"},
                    { "time":"19:00-22:00", "bus":"每 1h 一班"}
                ]
            }
        }
        retjson = {'code': 200, 'content': bus_json}
        self.write(json.dumps(retjson, ensure_ascii=False, indent=2))

