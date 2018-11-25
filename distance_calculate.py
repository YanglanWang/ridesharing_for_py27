#-*- coding: UTF-8 -*-
import math
import urllib2
import json


# 计算曼哈顿距离, 经度距离+纬度距离，单位：米
def manhattan_calculate( position_1, position_2 ):
    R_earth = 6371000
    velocity=8.33

    # position 第一个数是经度，第二个是纬度
    # 纬度距离
    d_1 = 2 * math.pi * R_earth * abs( position_2[1] - position_1[1] ) / 360

    # 经度距离
    # 注意cos的参数是弧度值
    d_2 = 2 * math.pi * R_earth * math.cos( math.radians( position_1[1] ) ) * abs(
        position_2[0] - position_1[0] ) / 360

    distance = d_1 + d_2
    duration = distance / velocity

    # return distance, duration
    return duration


def api_calculate( position_1, position_2 ):
    # 调用api时，经纬度的最多取6位
    urlRequest = 'http://restapi.amap.com/v3/direction/driving?key=a37de205f70806a79db53f2d0f847d80&origin=' + str(
        round( position_1[0], 6 ) ) + ',' + str( round( position_1[1], 6 ) ) + '&destination=' + str(
        round( position_2[0], 6 ) ) + ',' + str( round( position_2[1], 6 ) )

    res = urllib2.urlopen( urlRequest, data = None, timeout = 5 )
    data = res.read()
    data = json.loads( data )

    # 距离
    distance = data['route']['paths'][0]['distance']
    # 时间
    duration = data['route']['paths'][0]['duration']
    res.close()

    # return float( distance ), \
    return float( duration )