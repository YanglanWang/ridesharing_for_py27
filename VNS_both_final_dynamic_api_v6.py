# -*- coding: utf-8 -*-
"""
@author: yanglan

插入法+VNS
"""
"""
先出机场后去机场的模式：

曼哈顿距离
速度设为30公里每小时, 8.33米每秒
使用总行驶距离作为成本，使用行驶时间矩阵计算时间窗等

入机场者：
"xx-xx时间段内上车出发"，取出租车上车时间的前5分钟，后10分钟
行驶时间不超过单人单车直达的1.5倍

出机场者：
出发时间窗设定为出租车出发时间的前5分钟，后10分钟
到达时间窗设为行驶距离不超过单人单车直达的行驶距离的1.5倍

每个顾客点的服务时间为半分钟
输出：车辆数，每个路线的顾客点编号顺序，在每个点的时间范围（出发时间范围，回机场时间范围，到达每个顾客点的时间范围）, 总路程的平均乘客数
"""
"""
删掉了之前的程序中所有用于debug的注释
"""

import time
import math
import numpy as np
import copy

# import pylab
from matplotlib import pylab

import urllib2
import json
import logging

import read_file_py
import someclass
# import check2distance

car_capacity = 7
service_time = 30
# 最大时间窗空余量
max_timeWindow_interval = 60
# 最大等待时间
max_waiting_time = 3600
# 假设固定速度
velocity = 8.33

maxIteration = 7

# 选取时间段
time_point_in_1 = "2015-08-03 18:00:00"
time_point_in_2 = "2015-08-03 18:30:00"

time_point_out_1 = "2015-08-03 16:00:00"
time_point_out_2 = "2015-08-03 16:30:00"


def getUrl_multiTry( url ):
    # user_agent ='"Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 Safari/537.36"'
    user_agent = '"Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0"'
    headers = {'User-Agent': user_agent}
    maxTryNum = 10
    for tries in range( maxTryNum ):
        try:
            req = urllib2.Request( url, headers = headers )
            html = urllib2.urlopen( req ).read()
            break
        except:
            if tries < (maxTryNum - 1):
                continue
            else:
                logging.error( "Has tried %d times to access url %s, all failed!", maxTryNum, url )
                break

    return html

def check2distance(a, distance_dictionary):
    can_insert = 1
    # expected_return_time=0
    time_list = []
    whole_distance = distance_dictionary['airport' + '_' + a.route_list[0].id]
    time_list.append(whole_distance)
    if len(a.route_list) == 1:
        whole_distance = whole_distance + distance_dictionary[a.route_list[0].id + '_' + 'airport']
        time_list.append(whole_distance)
    else:
        while can_insert == 1:
            for k in range(0, len(a.route_list) - 1):
                whole_distance = whole_distance + distance_dictionary[
                    a.route_list[k].id + '_' + a.route_list[k + 1].id]
                if whole_distance > 4 * distance_dictionary['airport' + '_' + a.route_list[k+1].id]:
                    time_list = []
                    can_insert = 0

                else:
                    time_list.append( whole_distance )
                    if k==len(a.route_list)-2:
                        whole_distance = whole_distance + distance_dictionary[a.route_list[k + 1].id + '_' + 'airport']
                        time_list.append(whole_distance)
    return can_insert, time_list


def plot_a_simple_map( ready_route, filename ):
    airport_position = [113.814, 22.623]
    multiplier = math.cos( math.radians( airport_position[1] ) )
    x = [113.814 * multiplier]
    y = [22.623]
    for j in range( 0, len( ready_route.route_list ) ):
        x.append( ready_route.route_list[j].position[0] * multiplier )
        y.append( ready_route.route_list[j].position[1] )
        if ready_route.route_list[j].service_type == True:
            label = 'r*'
        else:
            label = 'g*'
    x.append( 113.814 * multiplier )
    y.append( 22.623 )

    pylab.plot( x, y, label )
    pylab.plot( x, y, '--' )
    pylab.plot( 113.814 * multiplier, 22.623, 'ko' )

    pylab.title( filename )
    pylab.axis( 'off' )
    pylab.show()


def calculate_cutomer_out( customer_out_calculating, whole_route, distance_dictionary,
                           customer_out_calculated_route_id ):

    distance_test = float( "inf" )
    for i in range( 0, len( customer_out_calculating ) ):  # 表示现有需要计算的订单

        if (len( whole_route ) == 0):
            # key = 'airport' + '_' + customer_out_calculating[i].id
            route_list_tmp = []
            route_list_tmp.append( customer_out_calculating[0] )
            time_list = []
            expected_drop_time0 = distance_dictionary['airport' + '_' + customer_out_calculating[0].id]
            time_list.append( expected_drop_time0 )
            route_tmp = someclass.Route( customer_out_calculated_route_id, route_list_tmp, time_list )
            route_tmp0 = []
            route_tmp0.append( route_tmp )
            whole_route[0] = route_tmp0

            # customer_out_calculated.append( customer_out_calculated_route_id, route )
            customer_out_calculated_route_id = customer_out_calculated_route_id + 1
        else:
            for a in whole_route[0]:  # 不同的线路
                for j in range( 0, len( a.route_list ) + 1 ):
                    if j == 0:
                        distance_increase = distance_dictionary['airport' + '_' + customer_out_calculating[i].id] + \
                                            distance_dictionary[customer_out_calculating[i].id + '_' + a.route_list[0].id] - \
                                            distance_dictionary['airport' + '_' + a.route_list[0].id]
                    if j == len( a.route_list ):
                        distance_increase = distance_dictionary[
                                                a.route_list[-1].id + '_' + customer_out_calculating[i].id] + \
                                            distance_dictionary[
                                                customer_out_calculating[i].id + '_' + 'airport'] - distance_dictionary[
                                                a.route_list[-1].id + '_' + 'airport']
                    if (j != 0) and (j != len( a.route_list )):
                        distance_increase = distance_dictionary[
                                                a.route_list[j - 1].id + '_' + customer_out_calculating[
                                                    i].id] + distance_dictionary[
                                                customer_out_calculating[i].id + '_' + a.route_list[j].id] - \
                                            distance_dictionary[
                                                a.route_list[j - 1].id + '_' + a.route_list[j].id]

                    if distance_increase < distance_test:
                        distance_test = distance_increase
                        insert_position = j
                        insert_route = a
                        insert_route_index = whole_route[0].index( insert_route )

            insert_route.route_list.insert(insert_position, customer_out_calculating[i])
            # customer_out_calculated[a].insert( j, customer_out_calculating[i] )
            can_insert, time_list = check2distance(insert_route, distance_dictionary)
            if can_insert == 0:
                # a.route_list.pop(insert_position)
                customer_out_cannot_service.append(customer_out_calculating[i])
            else:
                # a.route_drop_time_list=time_list
                whole_route[0][insert_route_index].route_list.insert(insert_position, customer_out_calculating[i])
                whole_route[0][insert_route_index].drop_time_list = time_list
    whole_route[1] = whole_route[0]
    whole_route[0] = None

    return whole_route, customer_out_cannot_service


def calculate_cutomer_in(customer_in_calculating, whole_route, distance_dictionary):
    distance_test = float( "inf" )
    for i in range( 0, len( customer_in_calculating ) ):  # 表示现有需要计算的订单
        for a in whole_route[1]:
            if customer_in_calculating[i].on_time < a.drop_time_list[-1]:
                if customer_in_calculating[i].on_time < a.drop_time_list[0]:
                    distance_increase = distance_dictionary['airport' + '_' + customer_in_calculating[i].id] + \
                                        distance_dictionary[customer_in_calculating[i].id + '_' + a.route_list[0].id] - \
                                        distance_dictionary['airport' + '_' + a.route_list[0].id]
                    p = 0
                else:
                    for j in range( 0, len( a.drop_time_list ) - 1 ):
                        if (customer_in_calculating[i].on_time > a.drop_time_list[j]) and \
                                (customer_in_calculating[i].on_time < a.drop_time_list[j + 1]):
                            if j == len( a.drop_time_list ) - 2:
                                distance_increase = distance_dictionary[
                                                        a.route_list[-1] + '_' + customer_in_calculating[j]] + \
                                                    distance_dictionary[customer_in_calculating[j] + '_' + 'airport'] - \
                                                    distance_dictionary[a.route_list[-1] + '_' + 'airport']
                            else:
                                distance_increase = distance_dictionary[
                                                        a.route_list[j].id + '_' + customer_in_calculating[i].id] + \
                                                    distance_dictionary[
                                                        customer_in_calculating[i].id + '_' + a.route_list[j + 1].id] - \
                                                    distance_dictionary[
                                                        a.drop_time_list[j].id + '_' + a.drop_time_list[
                                                            j + 1].id]

                            p = j + 1

                if distance_increase < distance_test:
                    distance_test = distance_increase
                    insert_route = a
                    insert_position = p
                    insert_route_index = whole_route[0].index( insert_route )

        temp_route = insert_route.route_list( insert_position, customer_in_calculating[i] )
        can_insert, time_list = check2distance( temp_route, distance_dictionary )
        if can_insert == 0:
            customer_in_cannot_service.append( customer_in_calculating[i] )
        else:
            # whole_route[1][whole_route[1].index( a )].route_list.insert( insert_position, customer_in_calculating[i] )
            whole_route[1][insert_route_index].route_list.insert( insert_position, customer_in_calculating[i] )
            whole_route[1][insert_route_index].drop_time_list = time_list

    whole_route[2] = whole_route[1]
    whole_route[1] = None

    return whole_route, customer_in_cannot_service


distance_dictionary = dict()

"""
========================== 读取所有出入机场数据 ======================================
"""
start = time.clock()
customer = []

f = open( 'both mode_1123.txt', 'w' )
f.write( "2015-08-03" + '\n' )

filename_out = '20150803_gaode_offboard.txt'  # 出机场的数据
filename_in = '20150803_gaode_onboard.txt'  # 入机场的数据

customer_out, distance_dictionary = read_file_py.read_file( filename_out, True, distance_dictionary )
customer_in, distance_dictionary = read_file_py.read_file( filename_in, False, distance_dictionary )
customer = customer_out + customer_in

f.write( "出机场总点数：" + str( len( customer_out ) ) + '\n' )
f.write( "入机场总点数：" + str( len( customer_in ) ) + '\n' )

end = time.clock()
f.write( "读取数据耗时：" + str( end - start ) + '\n' + '\n' )

"""
========================== 读取数据结束，开始大循环 ======================================
"""
"""
"2015-08-03 00:00:00" 对应时间戳 1438531200.0 
"2015-08-04 00:00:00" 对应时间戳 1438617600.0 

数据更新间隔5分钟，300秒

假设出机场的提前半小时下订单
假设入机场的提前2小时下单

假定入机场的上车点平均单程为1小时
晚10点半以后(10点以后预约)的出机场数据不要

距出发时间还有5分钟时，车辆固定，准备出发

"""

customer_out_calculating = []  # 无顺序
#    customer_out_calculated=dict()#有顺序的各种不同线路
customer_out_calculated_route_id = 0
customer_out_cannot_service = []
customer_in_cannot_service = []
route = []
customer_in_calculating = []
customer_in_cannot_service = []
customer_out_calculated_route_id = 0
for timestamp_1 in range( 1438531200, 1438617600, 900 ):
    # 每隔15min算一次

    start = time.clock()
    """时间戳表示实际时间，现实时间"""
    timestamp_2 = timestamp_1 + 900
    timestr_1 = time.strftime( "%H:%M:%S", time.localtime( timestamp_1 ) )
    timestr_2 = time.strftime( "%H:%M:%S", time.localtime( timestamp_2 ) )
    f.write( "当前时间：" + timestr_1 + "--" + timestr_2 + '\n' )
    print("当前时间：" + timestr_1 + "--" + timestr_2)

    whole_route = dict()
    for r in customer_out:
        if timestamp_1 < r.on_time < timestamp_2:
            customer_out_calculating.append( r )
    f.write( "此时段的出机场订单有：" + str( len( customer_out_calculating ) ) + '个\n' )

    whole_route, customer_out_cannot_service = calculate_cutomer_out( customer_out_calculating, whole_route,
                                                                      distance_dictionary,
                                                                      customer_out_calculated_route_id )
    f.write( "在此时间间隔内不能服务的出机场乘客是：" )
    for i in range( len( customer_out_cannot_service ) ):
        f.write( customer_out_cannot_service[i].id + ', ' )

    print("在此时间间隔内不能服务的出机场乘客是：")
    for i in range( len( customer_out_cannot_service ) ):
        print(customer_out_cannot_service[i].id + ', ')
    # this is not fully true! #we should select customer_in based on each route in whole_route[1]. Selecting customer from all customer_in
    # without aiming at specific route will introduce much inefficient action.
    latest_return_time = 0
    for a in whole_route[1]:
        if a.drop_time_list[-1] > latest_return_time:
            latest_return_time = a.drop_time_list[-1]

    for r in customer_in:
        if timestamp_1 < r.on_time < latest_return_time:
            customer_in_calculating.append( r )
    for r in customer_in_cannot_service:
        if timestamp_1 < r.on_time < latest_return_time:
            customer_in_calculating.append( r )

    f.write( "此时段的入机场订单可能有：" + str( len( customer_in_calculating ) ) + '个\n' )

    whole_route, customer_in_cannot_service = calculate_cutomer_in( customer_in_calculating, whole_route,
                                                                    distance_dictionary )
    image_name = timestr_1 + "--" + timestr_2 + " final"
    for ready_route in whole_route[2]:
        plot_a_simple_map( ready_route, image_name )

print("在整个模拟中，一直达不到进机场条件的订单有：")
for i in range( len( customer_in_cannot_service ) ):
    print(customer_in_cannot_service[i].id + ", ")

f.write( "在整个模拟中，一直达不到进机场条件的订单有：" )
for i in range( len( customer_in_cannot_service ) ):
    f.write( customer_in_cannot_service[i].id + ", " )
