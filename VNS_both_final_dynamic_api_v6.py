# -*- coding: utf-8 -*-
"""
@author: jq

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
# from matplotlib import pylab

import urllib2
import json
import logging

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



def getUrl_multiTry(url):
    #user_agent ='"Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 Safari/537.36"'  
    user_agent ='"Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0"'
    headers = { 'User-Agent' : user_agent }  
    maxTryNum=10  
    for tries in range(maxTryNum):  
        try:  
            req = urllib2.Request(url, headers = headers)   
            html=urllib2.urlopen(req).read()  
            break  
        except:  
            if tries <(maxTryNum-1):  
                continue  
            else:  
                logging.error("Has tried %d times to access url %s, all failed!",maxTryNum,url)  
                break  
              
    return html 




#计算两点间的行驶时间，单位：秒
def driving_time(position_1, position_2):
    
    #调用api时，经纬度的最多取6位
    urlRequest = 'http://restapi.amap.com/v3/direction/driving?key=a37de205f70806a79db53f2d0f847d80&origin=' + str(
        round(position_1[0],6)) +','+str(round(position_1[1],6))+'&destination='+str(round(position_2[0],6)) +','+str(round(position_2[1],6))
    #res = urllib2.urlopen(urlRequest, data=None, timeout=200)
    #res = urllib2.urlopen(urlRequest, data=None)
    data=getUrl_multiTry(urlRequest)
    #data = res.read()
    data = json.loads(data)
    
    #距离
    distance= data['route']['paths'][0]['distance']
    #时间
    duration= data['route']['paths'][0]['duration']
    # res.close()
    
    return float(distance), float(duration)
    
    
# 计算曼哈顿距离, 经度距离+纬度距离，单位：米
def manhattan_calculate(position_1, position_2):
    
    R_earth = 6371000
    
    # position 第一个数是经度，第二个是纬度
    # 纬度距离
    d_1 = 2 * math.pi * R_earth * abs(position_2[1] - position_1[1]) / 360
    
    # 经度距离
    # 注意cos的参数是弧度值
    d_2 = 2 * math.pi * R_earth * math.cos(math.radians(position_1[1])) * abs(position_2[0] - position_1[0]) / 360
    
    distance = d_1 + d_2
    duration = distance / velocity
    
    return distance, duration


# 一个线路route指的是一个整数向量，给出的是顾客点的顺序，用cuntomer向量中的index表示, route从0开始从0结束
# 一个解solution指的是若干个route放在一起的list，每个route就是一个车的路线
# route solution time_data等都是list


# 给定一个新线路，判断是否可行(时间窗，capacity), 若可行，返回True；若不可行，返回FALSE。
# route 至少2个点，[0,x,0]
def judge_feasibility(route, customer, distance_matrix, distance_airport, time_matrix, time_airport, number_out):
    
    n_tmp = len(route)
    first_onboard_customer = n_tmp-1 # 该车所接的第一个入机场的乘客在route中的位置   # 不是在customer中的位置
            
    if n_tmp == 2 or n_tmp == 3:
        return True
		
    # 必须先是出机场的点，后是入机场的点，以编号值小于/大于等于number_out作为分别方法
    # 出入机场的点的个数，分别不能超过car_capacity
    else:
        for i in range(1, n_tmp-1):
            if route[i] >= number_out:
                first_onboard_customer = i
                for j in range(first_onboard_customer +1, n_tmp-1):
                    if route[j] < number_out:
                        return False
                break
    # first_onboard_customer 保存了下来，若为n_tmp-1，表示该route没有入机场的订单任务；若为1，表示没有出机场的订单任务
            
    # capacity 检验
    if first_onboard_customer > car_capacity +1 or n_tmp - first_onboard_customer > car_capacity +1:
        return False

    # 乘客从机场出发的时间窗应该有交集，且交集至少1分钟
    early_start_window = []
    late_start_window = []
    
    # 出机场时间窗
    for i in range(1, first_onboard_customer):
        early_start_window.append( customer[route[i]][1][0] )
        late_start_window.append( customer[route[i]][1][1] )
    
    if len(early_start_window) > 0:
        start_time_0 = max(early_start_window)
        start_time_1 = min(late_start_window)
    else:
        # 若没有出机场的乘客，则出发时间与第一个点（入机场点）保持一致
        # start_time_0 = 0
        # start_time_1 = float("inf")
        start_time_0 = customer[route[1]][1][0] - time_airport[route[1]][0]
        start_time_1 = customer[route[1]][1][1] - time_airport[route[1]][0]
        
    # 时间窗至少留有1分钟的空余量
    if start_time_0 > (start_time_1 - max_timeWindow_interval) :
        return False
        
    # 先从前往后算出机场的乘客在各点的到达时间范围
    # 并判别行驶时间的限制
    time_interval_out = [[start_time_0, start_time_1]]
    if first_onboard_customer > 1:
        time_interval_out.append([start_time_0 + time_airport[route[1]][0],
                                  start_time_1 + time_airport[route[1]][0]])
        if first_onboard_customer > 2:
            for i in range(2, first_onboard_customer):
                time_interval_out.append([time_interval_out[i-1][0] + time_matrix[ route[i-1]][route[i] ] + service_time,
                                          time_interval_out[i-1][1] + time_matrix[ route[i-1]][route[i] ] + service_time])
                if customer[route[i]][2] < time_interval_out[i][0] - start_time_0:
                    return False
    
    # print first_onboard_customer
    # 记录入机场的乘客的上车时间窗
    if first_onboard_customer < n_tmp-1:  #若没有入机场的，后面一大段直接跳过，返回True
        time_interval_in = []
        for i in range(first_onboard_customer, n_tmp-1):
            # time_interval_in.append(customer[route[i]][1]) 这是错误的，因为customer[...][1]是数组，是浅赋值，后面会改变customer数组
            time_interval_in.append([customer[route[i]][1][0], customer[route[i]][1][1]])
        
        time_interval_tmp = time_interval_out + time_interval_in   # n_tmp -1对值，回到机场的时间没算   #与route的编号保持一致
        
        # 从最后一个出机场顾客点开始，更新后续每个点的到达时间窗下限
        if first_onboard_customer > 1:  # 如果有出机场的乘客，则包含出机场至入机场的中间路段
            t_tmp_1 = time_interval_tmp[first_onboard_customer-1][0] + time_matrix[route[first_onboard_customer-1]][route[first_onboard_customer]] + service_time
            
            if t_tmp_1 > time_interval_tmp[first_onboard_customer][0]:
                time_interval_tmp[first_onboard_customer][0] = t_tmp_1
                
            # 顺便判断最大等待时间
            elif time_interval_tmp[first_onboard_customer][0] - t_tmp_1 > max_waiting_time:
                return False
        
            # 从入机场部分开始
        for i in range(first_onboard_customer, n_tmp-2): # 若first_onboard_customer==n_tmp-2, 即只有一个入机场的人，则这段会跳过不执行
            t_tmp_1 = time_interval_tmp[i][0] + time_matrix[route[i]][route[i+1]] + service_time
            if t_tmp_1 > time_interval_tmp[i+1][0]:
                time_interval_tmp[i+1][0] = t_tmp_1
                
            # 顺便判断最大等待时间
            elif time_interval_tmp[i+1][0] - t_tmp_1 > max_waiting_time:
                return False
        
        # 从最后一个顾客开始，往前更新之前每个入机场顾客点的到达时间窗上限
        for i in range(0, n_tmp-3):
            t_tmp_2 = time_interval_tmp[n_tmp-2-i][1] - time_matrix[route[n_tmp-3-i]][route[n_tmp-2-i]] - service_time
            if t_tmp_2 < time_interval_tmp[n_tmp-3-i][1]:
                time_interval_tmp[n_tmp-3-i][1] = t_tmp_2
        
        ## ！！！从1回到0用的不是time_matrix，是time_airport
        t_tmp_2 = time_interval_tmp[1][1] - time_airport[route[1]][0] - service_time
        if t_tmp_2 < time_interval_tmp[0][1]:
            time_interval_tmp[0][1] = t_tmp_2
        
        # 每个时间窗长度应该大于阈值
        for i in range(0, n_tmp-1):
            if time_interval_tmp[i][1] - time_interval_tmp[i][0] < max_timeWindow_interval:
                # if i==0 and time_interval_tmp[i][1] > time_interval_tmp[i][0]:
                    # print [time.strftime("%H:%M:%S", time.localtime(time_interval_tmp[i][0] + 1438500000.0)),
                           # time.strftime("%H:%M:%S", time.localtime(time_interval_tmp[i][1] + 1438500000.0))]
                return False
        
        # 计算从每个入机场顾客点出发，累计到达机场的时间，用上限与下限分别算，都应该小于最长行驶时间
        time_back_to_airport = [time_interval_tmp[n_tmp-2][0] + time_airport[route[-2]][1] + service_time,
                                time_interval_tmp[n_tmp-2][1] + time_airport[route[-2]][1] + service_time]
        
        for i in range(first_onboard_customer, n_tmp-2):  #i=n_tmp-2可以跳过，因为离机场最近
            t_tmp_1 = time_back_to_airport[0] - time_interval_tmp[i][0]
            t_tmp_2 = time_back_to_airport[1] - time_interval_tmp[i][1]
            if t_tmp_1 > customer[route[i]][2] or t_tmp_2 > customer[route[i]][2]:
                return False
        # if route == [0, 11, 8, 18, 15, 45, 0]:
            # print "============"
        
    # if route == [0, 11, 8, 18, 15, 45, 0]:
        # print "-------------"
            
    return True

# 已知route可行，计算每个route的出发时间范围
# len>=3
def route_start_time(route, customer, time_matrix, time_airport, number_out):
    
    n_tmp = len(route)
    first_onboard_customer = n_tmp-1 # 该车所接的第一个入机场的乘客在route中的位置   # 不是在customer中的位置
    
    for i in range(1, n_tmp-1):
        if route[i] >= number_out:
            first_onboard_customer = i
            break
        
    early_start_window = []
    late_start_window = []
    
    # 出机场时间窗
    for i in range(1, first_onboard_customer):
        early_start_window.append( customer[route[i]][1][0] )
        late_start_window.append( customer[route[i]][1][1] )
    if len(early_start_window) > 0:
        start_time_0 = max(early_start_window)
        start_time_1 = min(late_start_window)
    else:
        # 若没有出机场的乘客，则出发时间与第一个点（入机场点）保持一致
        # start_time_0 = 0
        # start_time_1 = float("inf")
        start_time_0 = customer[route[1]][1][0] - time_airport[route[1]][0]
        start_time_1 = customer[route[1]][1][1] - time_airport[route[1]][0]
        
    # 先从前往后算出机场的乘客在各点的到达时间范围
    time_interval_out = [[start_time_0, start_time_1]]
    if first_onboard_customer > 1:
        time_interval_out.append([start_time_0 + time_airport[route[1]][0],
                                  start_time_1 + time_airport[route[1]][0]])
        if first_onboard_customer > 2:
            for i in range(2, first_onboard_customer):
                time_interval_out.append([time_interval_out[i-1][0] + time_matrix[ route[i-1]][route[i] ] + service_time,
                                          time_interval_out[i-1][1] + time_matrix[ route[i-1]][route[i] ] + service_time])
    
    time_interval_tmp = time_interval_out
    # 记录入机场的乘客的上车时间窗
    if first_onboard_customer < n_tmp-1:  #若没有入机场的，后面一大段直接跳过
        time_interval_in = []
        for i in range(first_onboard_customer, n_tmp-1):
            time_interval_in.append([customer[route[i]][1][0], customer[route[i]][1][1]])
        
        time_interval_tmp = time_interval_out + time_interval_in   # n_tmp -1对值，回到机场的时间没算   #与route的编号保持一致
            
        # 从最后一个顾客开始，往前更新之前每个顾客点的到达时间窗上限
        for i in range(0, n_tmp-3):
            t_tmp_2 = time_interval_tmp[n_tmp-2-i][1] - time_matrix[route[n_tmp-3-i]][route[n_tmp-2-i]] - service_time
            if t_tmp_2 < time_interval_tmp[n_tmp-3-i][1]:
                time_interval_tmp[n_tmp-3-i][1] = t_tmp_2
        
        ## ！！！从1回到0用的不是time_matrix，是time_airport
        t_tmp_2 = time_interval_tmp[1][1] - time_airport[route[1]][0] - service_time
        if t_tmp_2 < time_interval_tmp[0][1]:
            time_interval_tmp[0][1] = t_tmp_2
    
    return time_interval_tmp[0]

        
 
# 已知route可行，计算每一个点的arrive time intervals # [出发时间范围，中间每个点的到达时间范围，回机场的时间范围]，在每个接人地点的最大等待时间
# 代码与检验可行性的代码高度重复
# 已知 len(route) >= 3
def route_time_intervals(route, customer, time_matrix, time_airport, number_out):

    n_tmp = len(route)
    first_onboard_customer = n_tmp-1 # 该车所接的第一个入机场的乘客在route中的位置   # 不是在customer中的位置
    
    for i in range(1, n_tmp-1):
        if route[i] >= number_out:
            first_onboard_customer = i
            break
        
    early_start_window = []
    late_start_window = []
    
    # 出机场时间窗
    for i in range(1, first_onboard_customer):
        early_start_window.append( customer[route[i]][1][0] )
        late_start_window.append( customer[route[i]][1][1] )
    if len(early_start_window) > 0:
        start_time_0 = max(early_start_window)
        start_time_1 = min(late_start_window)
    else:
        # 若没有出机场的乘客，则出发时间与第一个点（入机场点）保持一致
        # start_time_0 = 0
        # start_time_1 = float("inf")
        start_time_0 = customer[route[1]][1][0] - time_airport[route[1]][0]
        start_time_1 = customer[route[1]][1][1] - time_airport[route[1]][0]
        
    # 先从前往后算出机场的乘客在各点的到达时间范围
    # 并判别行驶时间的限制
    time_interval_out = [[start_time_0, start_time_1]]
    if first_onboard_customer > 1:
        time_interval_out.append([start_time_0 + time_airport[route[1]][0],
                                  start_time_1 + time_airport[route[1]][0]])
        if first_onboard_customer > 2:
            for i in range(2, first_onboard_customer):
                time_interval_out.append([time_interval_out[i-1][0] + time_matrix[ route[i-1]][route[i] ] + service_time,
                                          time_interval_out[i-1][1] + time_matrix[ route[i-1]][route[i] ] + service_time])
    
    time_interval_tmp = time_interval_out
    waiting_time = []
    # 记录入机场的乘客的上车时间窗
    if first_onboard_customer < n_tmp-1:  #若没有入机场的，后面一大段直接跳过
        time_interval_in = []
        for i in range(first_onboard_customer, n_tmp-1):
            time_interval_in.append([customer[route[i]][1][0], customer[route[i]][1][1]])
        
        time_interval_tmp = time_interval_out + time_interval_in   # n_tmp -1对值，回到机场的时间没算   #与route的编号保持一致
        
        waiting_time = [0]
        # 从最后一个出机场顾客点开始，更新后续每个点的到达时间窗下限
            # 如果有出机场的乘客，则包含出机场至入机场的中间路段
        if first_onboard_customer > 1:  
            t_tmp_1 = time_interval_tmp[first_onboard_customer-1][0] + time_matrix[route[first_onboard_customer-1]][route[first_onboard_customer]] + service_time
            if t_tmp_1 > time_interval_tmp[first_onboard_customer][0]:
                time_interval_tmp[first_onboard_customer][0] = t_tmp_1
            else:
                waiting_time[0] = time_interval_tmp[first_onboard_customer][0] - t_tmp_1
        
            # 从入机场部分开始
        for i in range(first_onboard_customer, n_tmp-2): # 若first_onboard_customer==n_tmp-2, 即只有一个入机场的人，则这段会跳过不执行
            t_tmp_1 = time_interval_tmp[i][0] + time_matrix[route[i]][route[i+1]] + service_time
            if t_tmp_1 > time_interval_tmp[i+1][0]:
                time_interval_tmp[i+1][0] = t_tmp_1
                waiting_time.append(0)
            else:
                waiting_time.append(time_interval_tmp[i+1][0] - t_tmp_1)
            
        # 从最后一个顾客开始，往前更新之前每个入机场顾客点的到达时间窗上限
        for i in range(0, n_tmp-3):
            t_tmp_2 = time_interval_tmp[n_tmp-2-i][1] - time_matrix[route[n_tmp-3-i]][route[n_tmp-2-i]] - service_time
            if t_tmp_2 < time_interval_tmp[n_tmp-3-i][1]:
                time_interval_tmp[n_tmp-3-i][1] = t_tmp_2
        
        ## ！！！从1回到0用的不是time_matrix，是time_airport
        t_tmp_2 = time_interval_tmp[1][1] - time_airport[route[1]][0] - service_time
        if t_tmp_2 < time_interval_tmp[0][1]:
            time_interval_tmp[0][1] = t_tmp_2
    
    # 把最后回到机场的那段加上
    time_back_to_airport = [time_interval_tmp[n_tmp-2][0] + time_airport[route[-2]][1] + service_time,
                            time_interval_tmp[n_tmp-2][1] + time_airport[route[-2]][1] + service_time]
    time_interval_tmp.append(time_back_to_airport)
    
    return time_interval_tmp, waiting_time


 
# 已知route可行，计算在每个点的累计行驶距离，由小到大，【不包含等待时间】
def route_distance_data(route, distance_matrix, distance_airport):
    
    n_tmp = len(route)
    
    travel_cost = [0]
    travel_cost.append(distance_airport[route[1]][0])
    if n_tmp == 3:
        travel_cost.append(travel_cost[1] * 2)
    else:
        for i in range(2, n_tmp-1):
            travel_cost.append(travel_cost[i-1] + distance_matrix[ route[i-1]][route[i] ])
        
        travel_cost.append(travel_cost[n_tmp - 2] +  distance_airport[route[n_tmp - 2]][1])
                
    return travel_cost



# 已知route可行，计算总行驶时间，作为成本
def route_travel_distance(route, distance_matrix, distance_airport):
    
    if len(route) == 2:
        return 0.0
    else:
        this_data = route_distance_data(route, distance_matrix, distance_airport)
        return this_data[-1]



# 给定一个完整的解solution，及每个线路的时间数组的集合，计算目标函数值,
# solution是一个list，每个Route的长度不一定相同
    
    
# 计算初始解
# 在大循环中注意深拷贝与浅拷贝的问题
def initial_solution(customer, distance_matrix, distance_airport, time_matrix, time_airport, number_out):
    
    # 逐个构造route，插入至不能插入位置
    # 每插入一个新人，都要遍历所有未插入的顾客，选择最优的人的最优位置
    solution = []
    travel_cost_stored = []
    current_route = [0,0] #存储当前的路径
    unassigned_customer = range(0, len(customer))

    while(len(unassigned_customer)!=0):
        
        chosen_customer = -1 # 选择添加的顾客点
        opt_insertion = [0,0] #存储找到的最优的插入信息,[插入位置，插入的index值]
        opt_travel_cost = 1000000 # 任一超大的值
        
        route_reset_indicator = True # 在后面用于判断是否加新车，添新route
        
        # 每个未分配顾客都遍历每一个位置，选一个总行驶时间最小的
        for i in range(0, len(unassigned_customer)):
            chosen_customer = unassigned_customer[i] # 这个乘客在customer向量中的index
            
            for j in range(1, len(current_route)):
                
                current_route.insert(j, chosen_customer)
                judge_tmp = judge_feasibility(current_route, customer, distance_matrix, distance_airport, time_matrix, time_airport, number_out)
                
                if judge_tmp == True:
                    t_value = route_travel_distance(current_route, distance_matrix, distance_airport)
                    
                    # 若时间更短，则更新
                    if t_value < opt_travel_cost:
                        opt_insertion = [j, chosen_customer]
                        opt_travel_cost = t_value
                        route_reset_indicator = False # 仍有新的顾客点可以加进当前route里
                        
                current_route.pop(j) #去掉位置为j的用pop，去掉具体的值用remove

        if route_reset_indicator == False:
            current_route.insert(opt_insertion[0], opt_insertion[1])  #正式插入
            unassigned_customer.remove(opt_insertion[1]) # remove: 删掉数组的值，即删掉客户index

        else:
            # 存储当前route，新开一条route
            solution.append(current_route)
            t_value = route_travel_distance(current_route, distance_matrix, distance_airport) #计算总行驶时间
            travel_cost_stored.append(t_value)
            current_route = [0,0]
        
        # 注意最后一个route还没有加进去
        if len(unassigned_customer) == 0:
            solution.append(current_route)
            t_value = route_travel_distance(current_route, distance_matrix, distance_airport)
            travel_cost_stored.append(t_value)
    
    initialSolution = [solution, travel_cost_stored]
    return initialSolution
    

# 生成一个顾客一辆车的初始解，用于检验程序
def silly_initial_solution(customer, distance_matrix, distance_airport, number_out): 
    
    solution = []
    travel_cost_stored = []
    for i in range(0, len(customer)):
        solution.append([0,i,0])
        travel_cost_stored.append(route_travel_distance([0,i,0], distance_matrix, distance_airport))
    
    initialSolution = [solution, travel_cost_stored]
    return initialSolution



# VNS的几个算子 
# 当前选择的是遍历算子的所有可能
# route 是list，需要注意检验数组在函数内是否被改变
# 若返回的current_travel_cost值与原来一样，说明没变

# 单一route内交换
# len(route) >= 4

def operator_intra_exchange(route, current_travel_cost, customer, distance_matrix, distance_airport, time_matrix, time_airport, number_out):
    
    opt_index = [0,0,0,0]
    route_tmp = []
    new_route = route
    
    for step_1 in range(1, len(route)-2):  # 最大len-3
        for i in range(1, len(route)-step_1-1): # 最大len-step-2
            j = i + step_1 -1
            
            for m in range(j+1, len(route)-1):
                for n in range(m, len(route)-1):
                    
                    if m > j+1:
                        route_tmp = route[0:i] + route[m:n+1] + route[j+1:m] + route[i:j+1] + route[n+1:len(route)]
                    else:
                        route_tmp = route[0:i] + route[m:n+1] + route[i:j+1] + route[n+1:len(route)]
                    
                    judge_tmp = judge_feasibility(route_tmp, customer, distance_matrix, distance_airport, time_matrix, time_airport, number_out)
                    
                    if judge_tmp == True:
                        t_value = route_travel_distance(route_tmp, distance_matrix, distance_airport)
                        
                        if t_value < current_travel_cost:
                            current_travel_cost = t_value
                            opt_index = [i, j, m, n]
    
    if opt_index[0] != 0:
        i = opt_index[0]
        j = opt_index[1]
        m = opt_index[2]
        n = opt_index[3]
        
        if m > j+1:
            new_route = route[0:i] + route[m:n+1] + route[j+1:m] + route[i:j+1] + route[n+1:len(route)]
        else:
            new_route = route[0:i] + route[m:n+1] + route[i:j+1] + route[n+1:len(route)]
    
    return new_route, current_travel_cost


# 两个route交换
# len(route1),len(route2) >=3
# route可以变成[0,0]，表示删掉一个route
def operator_inter_exchange(route1, route2, travel_cost_1, travel_cost_2, customer, distance_matrix, distance_airport, time_matrix, time_airport, number_out):
    
    opt_index = [0,0,0,0]
    
    new_route_tmp_1 = []
    new_route_tmp_2 = []
    new_route_1 = route1
    new_route_2 = route2
    
    A_route_has_been_deleted = False
    
    for i in range(1, len(route1)-1): 
        for j in range(i-1, len(route1)-1): 
            
            for m in range(1, len(route2)-1):
                for n in range(m-1, len(route2)-1):
                    
                    new_route_tmp_1 = route1[0:i] + route2[m:n+1] + route1[j+1:len(route1)]
                    new_route_tmp_2 = route2[0:m] + route1[i:j+1] + route2[n+1:len(route2)]
                    
                    judge_tmp_1 = judge_feasibility(new_route_tmp_1, customer, distance_matrix, distance_airport, time_matrix, time_airport, number_out)
                    judge_tmp_2 = judge_feasibility(new_route_tmp_2, customer, distance_matrix, distance_airport, time_matrix, time_airport, number_out)
                    
                    if (judge_tmp_1 == True) and (judge_tmp_2 == True):
                        
                        t_value_1 = route_travel_distance(new_route_tmp_1, distance_matrix, distance_airport)
                        t_value_2 = route_travel_distance(new_route_tmp_2, distance_matrix, distance_airport)
                        
                        # 车数是第一目标，如果一个route被删了，则不管行驶时间，一定认为最优
                        if A_route_has_been_deleted == True:
                            if (len(new_route_tmp_1) == 2) or (len(new_route_tmp_2) == 2):
                                if (t_value_1 + t_value_2) < (travel_cost_1 + travel_cost_2):
                                    travel_cost_1 = t_value_1
                                    travel_cost_2 = t_value_2
                                    opt_index = [i, j, m, n]
                        else:
                            if (len(new_route_tmp_1) == 2) or (len(new_route_tmp_2) == 2):
                                A_route_has_been_deleted = True
                                travel_cost_1 = t_value_1
                                travel_cost_2 = t_value_2
                                opt_index = [i, j, m, n]
                                
                            elif (t_value_1 + t_value_2) < (travel_cost_1 + travel_cost_2):
                                travel_cost_1 = t_value_1
                                travel_cost_2 = t_value_2
                                opt_index = [i, j, m, n]
                        
        
    if opt_index[0] != 0:
        i = opt_index[0]
        j = opt_index[1]
        m = opt_index[2]
        n = opt_index[3]
        
        new_route_1 = route1[0:i] + route2[m:n+1] + route1[j+1:len(route1)]
        new_route_2 = route2[0:m] + route1[i:j+1] + route2[n+1:len(route2)]
        
    return new_route_1, new_route_2, travel_cost_1, travel_cost_2



# VNS求解
def VNS_calculate(initialSolution, customer, distance_matrix, distance_airport, time_matrix, time_airport, number_out):
    
    finalSolution = copy.copy(initialSolution[0])
    route_travel_cost = initialSolution[1] #相当于存储每条路线的cost
    
    f.write( "初始解车辆数：" + str(len(route_travel_cost)) + '\n')
    
    iteration_times = 0
    checked_iteration_times = 0
    which_iteration_deleted_vehicle_number = []
    
    while checked_iteration_times < maxIteration:
        
        iteration_times += 1
        
        #对每辆车，做route内变化
        for i in range(0, len(finalSolution)):
            
            finish_this_route = False
            
            while finish_this_route == False:
                current_route = finalSolution[i]
                current_travel_cost = route_travel_cost[i]
                
                new_route, new_travel_cost = operator_intra_exchange(current_route, current_travel_cost, customer, distance_matrix, distance_airport, time_matrix, time_airport, number_out)
                
                if current_travel_cost > new_travel_cost:
                    finalSolution[i] = new_route
                    route_travel_cost[i] = new_travel_cost
                else:
                    finish_this_route = True
        
        if len(finalSolution) > 1:
                
            # deleted_routes = []
            for i in range(0, len(finalSolution)-1):
                for j in range(i+1, len(finalSolution)):
                        
                    # 之前的循环中，如果已经删掉了这条线路，则跳过继续循环，每次只算Len至少为3的route数组
                    if len(finalSolution[i]) == 2:
                        # deleted_routes.append(i)
                        continue
                        
                    elif len(finalSolution[j]) == 2:
                        # deleted_routes.append(j)
                        continue
                        
                    current_route_1 = finalSolution[i]
                    current_route_2 = finalSolution[j]
                    current_travel_cost_1 = route_travel_cost[i]
                    current_travel_cost_2 = route_travel_cost[j]
                        
                    new_route_1, new_route_2, new_travel_cost_1, new_travel_cost_2 = operator_inter_exchange(current_route_1, current_route_2, current_travel_cost_1, current_travel_cost_2, customer, distance_matrix, distance_airport, time_matrix, time_airport, number_out)
                        
                    if current_travel_cost_1 != new_travel_cost_1:
                        finalSolution[i] = new_route_1
                        finalSolution[j] = new_route_2
                        route_travel_cost[i] = new_travel_cost_1
                        route_travel_cost[j] = new_travel_cost_2
                
            deleted_routes = []
            for i in range(0, len(finalSolution)):
                if len(finalSolution[i]) == 2:
                    deleted_routes.append(i)
            
            if len(deleted_routes) == 0:
                checked_iteration_times += 1
                    
            else:
                # deleted_routes = list(set(deleted_routes)) #去重复元素
                deleted_routes.sort(reverse=True)
                
                which_iteration_deleted_vehicle_number.append(iteration_times) # 记录这次减车的循环

                for i in range(0, len(deleted_routes)):
                    i_tmp = deleted_routes[i]
                    finalSolution.pop(i_tmp)
                    route_travel_cost.pop(i_tmp)
                
        else:  # 只有一辆车时
            checked_iteration_times = maxIteration
    
    f.write( "实际循环次数：" + str(iteration_times) + '\n')
    
    if len(which_iteration_deleted_vehicle_number) != 0:
        f.write( "第"+str(which_iteration_deleted_vehicle_number)+"次循环减少了车数"+'\n')
        
    f.write( "最终解车数：" + str(len(finalSolution))+'\n')
                      
    return finalSolution
  
    
                    
# def plot_a_simple_map(current_route, total_off, filename):
#
#     airport_position = [113.814, 22.623]
#     multiplier = math.cos(math.radians(airport_position[1]))
#     x=[113.814 * multiplier]
#     y=[22.623]
#     for j in range(1, len(current_route)-1):
#         x.append(total_off[ current_route[j] ][3][0] * multiplier)
#         y.append(total_off[ current_route[j] ][3][1])
#     x.append(113.814 * multiplier)
#     y.append(22.623)
#
#     pylab.plot(x, y, 'r*')
#     pylab.plot(x,y,'--')
#     pylab.plot(113.814 * multiplier, 22.623, 'ko')
#
#     pylab.title(filename)
#     pylab.axis('off')
#     pylab.show()
                    
                    
    
    
if __name__=="__main__":
    
    """
    ========================== 读取所有出机场数据 ======================================
    """
    start = time.clock()
    
    f=open('both mode_try5.txt', 'w')
    f.write( "2015-08-03" + '\n')
    
    filename = '20150803_gaode_offboard.txt' # 出机场的数据
    
    customer_ID_out=[]
    on_GPS_out=[]
    off_longitude=[]
    off_latitude=[]
    
    with open(filename, 'r') as file_to_read:
        
        j = 1 #用于添加用户ID
        while True:
            lines = file_to_read.readline() # 整行读取数据
            if not lines:
                break
                pass
            
            # 将整行数据分割处理，如果分割符是空格，括号里就不用传入参数，如果是逗号， 则传入‘，'字符。
            carNO_tmp, on_time_tmp, on_GPS_tmp, on_difference_tmp, on_longitude_tmp, on_latitude_tmp, off_time_tmp, off_GPS_tmp, off_difference_tmp, off_longitude_tmp, off_latitude_tmp, distance_tmp = [i for i in lines.split(',')]
            
            # 时间字符串-->时间戳数据
            timeArray = time.strptime(on_GPS_tmp[0:19], "%Y-%m-%dT%H:%M:%S")
            timestamp = time.mktime(timeArray)
            
            off_lo = float(off_longitude_tmp)
            off_la = float(off_latitude_tmp)
            
            if (110.0 < off_lo < 120.0) and (20 < off_la < 25):
               
                customer_ID_out.append('O_'+ on_GPS_tmp[11:13]+on_GPS_tmp[14:16]+on_GPS_tmp[17:19]) #用户ID
                j = j+1
                on_GPS_out.append(timestamp - 1438500000.0)  #数小一点便于计算？
                off_longitude.append(off_lo)
                off_latitude.append(off_la)
    
    f.write( "出机场总点数：" + str(len(customer_ID_out)) + '\n')
     
    off_longitude = np.array(off_longitude)
    off_latitude = np.array(off_latitude)
    
    total_off= np.vstack([off_longitude, off_latitude])
    total_off= np.transpose(total_off)

    """
    ========================== 读取所有入机场数据 ======================================
    """
    filename = '20150803_gaode_onboard.txt' # 入机场的数据
    
    customer_ID_in=[]
    on_GPS_in=[] 
    on_longitude=[]
    on_latitude=[]
    
    with open(filename, 'r') as file_to_read:
        
        j = 1 #用于添加用户ID
        while True:
            lines = file_to_read.readline() # 整行读取数据
            if not lines:
                break
                pass
            
            # 将整行数据分割处理，如果分割符是空格，括号里就不用传入参数，如果是逗号， 则传入‘，'字符。
            carNO_tmp, on_time_tmp, on_GPS_tmp, on_difference_tmp, on_longitude_tmp, on_latitude_tmp, off_time_tmp, off_GPS_tmp, off_difference_tmp, off_longitude_tmp, off_latitude_tmp, distance_tmp = [i for i in lines.split(',')]
            
            # 时间字符串-->时间戳数据
            timeArray = time.strptime(on_GPS_tmp[0:19], "%Y-%m-%dT%H:%M:%S")
            timestamp = time.mktime(timeArray)
            
            on_lo = float(on_longitude_tmp)
            on_la = float(on_latitude_tmp)
            
            if (110.0 < on_lo < 120.0) and (20 < on_la < 25):
               
                customer_ID_in.append('I_' + on_GPS_tmp[11:13]+on_GPS_tmp[14:16]+on_GPS_tmp[17:19]) #用户ID
                j = j+1
                on_GPS_in.append(timestamp - 1438500000.0)  #数小一点便于计算？
                on_longitude.append(on_lo)
                on_latitude.append(on_la)
    
    f.write( "入机场总点数：" + str(len(customer_ID_in)) + '\n')
     
    on_longitude = np.array(on_longitude) 
    on_latitude = np.array(on_latitude)
    
    total_on= np.vstack([on_longitude, on_latitude])
    total_on= np.transpose(total_on)
    
    end = time.clock()
    f.write( "读取数据耗时：" + str(end-start) + '\n' + '\n')
    
    
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
    # 输入： customer_ID_out, on_GPS_out, total_off, customer_ID_in, on_GPS_in, total_on
    
    current_customer = [] # [ID, [出发时间窗],行驶时间上限, 下车地点坐标]
    number_out = 0
    number_in = 0
    current_solution = [] # 存的是在current_customer中的index顺序
    start_time = [] # 每个route的出发时间
    distance_matrix = []
    distance_airport = []
    time_matrix = []
    time_airport = []
    
    CPU_time = [] #每轮循环的计算时间
    number_of_vehicles = 0 #车次数
    customer_num_served = [] #各个route服务的乘客数
    total_distance = []
    customer_num_weighted_distance = []
    num_of_API_used = [] # 距离函数/API调用次数
    nodes_number = [] #每轮计算的点数
    
    check_bug = []
    check_bug_2 = []
    
    for timestamp_1 in range(1438531200-1438500000, 1438617600-1438500000-7200, 300):
        
        start = time.clock()
        """时间戳表示实际时间，现实时间"""
        timestamp_2 = timestamp_1 + 300
        timestr_1 = time.strftime("%H:%M:%S", time.localtime(timestamp_1+1438500000))
        timestr_2 = time.strftime("%H:%M:%S", time.localtime(timestamp_2+1438500000))
        f.write( "当前时间：" + timestr_1 + "--" + timestr_2 + '\n')
        print "当前时间：" + timestr_1 + "--" + timestr_2
        
        f.write( "截至目前累积的出机场订单：" + str(number_in)+'\n')
        f.write( "截至目前累积的出机场订单：" + str(number_out)+'\n')
        """
        ======= 检验上一轮循环中的route，到时间的route则发车输出 ========
        """
        if len(current_solution) != 0:
            """出发的车，记录输出结果"""
            """预计还有5分钟到达出发时间下限，准备出发，路线固定下来"""
            """记录下这些路线所服务的乘客index，先不做更新矩阵的操作"""
            deleted_customer = [] 
            for i in range(0, len(current_solution)):
                if start_time[i][0] - 600 < timestamp_2:
                    
                    if start_time[i][0] < timestamp_2:
                        check_bug.append([timestr_1, timestr_2, [time.strftime("%H:%M:%S", time.localtime(start_time[i][0] + 1438500000.0)),
                                                                 time.strftime("%H:%M:%S", time.localtime(start_time[i][1] + 1438500000.0))] ])
                        check_bug_2.append(round((timestamp_2 - start_time[i][0]) / 60, 2))
                    
                    # 输出客户ID
                    settled_route = ["airport"]
                    for j in range(1, len(current_solution[i])-1):
                        settled_route.append(current_customer[ current_solution[i][j] ][0])
                    settled_route.append("airport")
                    f.write( "准备发车：" + str(settled_route) + '\n')
                    customer_num_served.append(len(settled_route)-2)
                    number_of_vehicles += 1
                    
                    plot_start_time=time.clock()
                    image_name=timestr_1 + "--" + timestr_2 + " final"
                    plot_a_simple_map(current_solution[i], current_customer, image_name)
                    plot_end_time=time.clock()
                    f.write("the time for picturing is"+str(plot_end_time-plot_start_time)+'\n')
                    
                    # 输出时间数据，转换成可读字符串
                    this_times, waiting_time = route_time_intervals(current_solution[i], current_customer, time_matrix, time_airport, number_out)
                    this_times_2 = []
                    for j in range(0, len(this_times)):
                        time_tmp = [time.strftime("%H:%M:%S", time.localtime(this_times[j][0] + 1438500000.0)),
                                    time.strftime("%H:%M:%S", time.localtime(this_times[j][1] + 1438500000.0))]
                        this_times_2.append(time_tmp)
                    f.write( "各点到达时间范围：" + str(this_times_2) + '\n')
                    f.write( "各个接客上车点的最大等待时间(秒）：" + str(waiting_time) + '\n')
                    
                    # 记录后面需要的数据
                    this_distances = route_distance_data(current_solution[i], distance_matrix, distance_airport)
                    total_distance.append(this_distances[-1])
                    f.write( "行驶距离：" + str(this_distances[-1]) + '\n')
        
                    final = 0
                    n_cus_out = 0
                    for j in range(1, len(this_distances) - 1):
                        if current_solution[i][j] >= number_out:
                            break
                        n_cus_out += 1
        
                    n_cus_tmp = n_cus_out # 某路段载客数
                    for j in range(0, len(this_distances)-1):
                        if j < n_cus_out:
                            final = final + (this_distances[j+1] - this_distances[j]) * n_cus_tmp
                            n_cus_tmp -= 1
                        else:
                            final = final + (this_distances[j+1] - this_distances[j]) * n_cus_tmp
                            n_cus_tmp += 1
            
                    customer_num_weighted_distance.append(final)
                    final = final / this_distances[-1]
                    f.write( "全程平均乘客数：" + str(final) + '\n')

                    # 已输出的客户点在矩阵中要删除
                    deleted_customer += current_solution[i][1:-1]
                    f.write( "==============================" + '\n')
                    
            """
            ================== 更新矩阵---删除 ==================
            list.pop(x) 删掉index是x的元素
            list.remove(x) 删掉值是x的元素
            
            """
            if len(deleted_customer) == 0:
                f.write( "没有车准备发车" + '\n')
            else:
                # 更新number_out与number_in的值
                n_tmp_1 = 0
                n_tmp_2 = 0
                for i in range(0, len(deleted_customer)):
                    if deleted_customer[i] < number_out:
                        n_tmp_1 += 1
                    else:
                        n_tmp_2 += 1
                number_out -= n_tmp_1
                number_in -= n_tmp_2
                f.write( "此次循环完成的出机场订单： " + str(n_tmp_1)+'\n')
                f.write( "此次循环完成的入机场订单： " + str(n_tmp_2)+'\n')
                
                # index从大到小排序，即从后往前删
                deleted_customer.sort(reverse=True)
                for i in range(0, len(deleted_customer)):
                    i_tmp = deleted_customer[i]
                    current_customer.pop(i_tmp)
                    distance_airport.pop(i_tmp)
                    time_airport.pop(i_tmp)
                    
                    distance_matrix.pop(i_tmp)
                    for j in range(0, len(distance_matrix)):
                        distance_matrix[j].pop(i_tmp)
                        
                    time_matrix.pop(i_tmp)
                    for j in range(0, len(time_matrix)):
                        time_matrix[j].pop(i_tmp)
                
        """
        ====================== 收取新订单 =====================
        输入： customer_ID_out, on_GPS_out, total_off, customer_ID_in, on_GPS_in, total_on
        """
        new_customer_ID_out = []
        new_time_window_out = []
        new_location_out = []
        """ 半小时后（假设的预约提前量）出发的订单"""
        # 晚上10点半以后的出机场数据不要了，因为匹配不上入机场的
        for i in range(0, len(on_GPS_out)):
            if timestamp_1+1800 <= on_GPS_out[i] < timestamp_2+1800 :
                new_customer_ID_out.append(customer_ID_out[i])
                new_time_window_out.append([on_GPS_out[i]-300, on_GPS_out[i]+300])
                new_location_out.append(total_off[i])
        f.write( "新出机场订单数量：" + str(len(new_customer_ID_out)) + '\n')
        
        new_customer_ID_in = []
        new_time_window_in = []
        new_location_in = []
        """ 2小时后（假设的预约提前量）出发的订单"""
        for i in range(0, len(on_GPS_in)):
            if timestamp_1+7200 <= on_GPS_in[i] < timestamp_2+7200:
                new_customer_ID_in.append(customer_ID_in[i])
                new_time_window_in.append([on_GPS_in[i]-300, on_GPS_in[i]+300])
                new_location_in.append(total_on[i])
        f.write( "新入机场订单数量：" + str(len(new_customer_ID_in)) + '\n')
        
        """
        ================== 更新矩阵---添加 =====================
        current_customer, distance_matrix, distance_airport, 
        time_matrix, time_airport 5个向量或矩阵的生成/更新
        list.insert(index,obj) 是插入指定的元素
        
        number_out number_in 
        
        输入new_customer_ID_out new_time_window_out new_location_out
        new_customer_ID_in new_time_window_in new_location_in
        """
        num_of_API_used_tmp = 0 # 记录调用API次数
        start_time_matrix=time.clock()
        
        if len(new_customer_ID_out) + len(new_customer_ID_in) != 0:  # 若为0，则矩阵不变
            
            # 若当前矩阵为空，则从头构建矩阵
            if len(current_customer) == 0:
                if len(current_solution) == 0:
                    f.write( "上一轮没有留下未分配订单"+'\n')
                else:
                    f.write( "上一轮有未分配订单，但发车后已无剩余"+'\n')
                    
                new_number_out = len(new_customer_ID_out)
                new_number_in = len(new_customer_ID_in)
                
                # 更新distance_airport, time_airport
                for i in range(0, new_number_out):
                    dis_tmp, time_tmp = driving_time([113.814, 22.623], new_location_out[i])
                    dis_tmp_2, time_tmp_2 = driving_time(new_location_out[i], [113.814, 22.623])
                    
                    distance_airport.append([dis_tmp, dis_tmp_2])
                    time_airport.append([time_tmp, time_tmp_2])
                    num_of_API_used_tmp += 2 #记录次数
                
                unvalid_orders = [] 
                for i in range(0, new_number_in):
                    dis_tmp, time_tmp = driving_time([113.814, 22.623], new_location_in[i])
                    dis_tmp_2, time_tmp_2 = driving_time(new_location_in[i], [113.814, 22.623])
                    
                    if time_tmp > 6600:
                        unvalid_orders.append(i)
                    
                    distance_airport.append([dis_tmp, dis_tmp_2])
                    time_airport.append([time_tmp, time_tmp_2])
                    num_of_API_used_tmp += 2 #记录次数
                
                # 到机场的直通行驶时间超过2小时（1小时50分）的 [入机场] 数据，删除
                if len(unvalid_orders)!= 0:
                    unvalid_orders.sort(reverse=True)
                    for i in range(0, len(unvalid_orders)):
                        i_tmp = unvalid_orders[i]
                        new_customer_ID_in.pop(i_tmp)
                        new_time_window_in.pop(i_tmp)
                        new_location_in.pop(i_tmp)
                        
                        distance_airport.pop(new_number_out + i_tmp)
                        time_airport.pop(new_number_out + i_tmp)
                        
                    f.write( "删掉超时订单后的新订单数：" + str(len(new_customer_ID_in)) + '\n')
                    new_number_in = len(new_customer_ID_in)
                    
                
                # customer向量：ID, 时间窗, 行驶时间上限, 地点坐标
                for i in range(0, new_number_out):
                    current_customer.append([new_customer_ID_out[i], new_time_window_out[i], time_airport[i][0]*1.5, new_location_out[i]])
                
                for i in range(0, new_number_in):
                    current_customer.append([new_customer_ID_in[i], new_time_window_in[i], time_airport[new_number_out + i][1]*1.5, new_location_in[i]])
                
                # 两个矩阵
                number_tmp = new_number_out + new_number_in
                distance_matrix = np.zeros([number_tmp, number_tmp])
                time_matrix = np.zeros([number_tmp, number_tmp])
                
                for i in range(0, number_tmp):
                    for j in range(0, number_tmp):
                        if i != j:
                            
                            if i < new_number_out:
                                position_1 = new_location_out[i]
                            else:
                                position_1 = new_location_in[i-new_number_out]
                                
                            if j < new_number_out:
                                position_2 = new_location_out[j]
                            else:
                                position_2 = new_location_in[j-new_number_out]
                
                            dis_tmp, time_tmp = driving_time(position_1, position_2)
                            distance_matrix[i][j] = dis_tmp
                            time_matrix[i][j] = time_tmp
                            num_of_API_used_tmp += 1 #记录次数
                            
                distance_matrix = distance_matrix.tolist()
                time_matrix = time_matrix.tolist()
                
                number_out = new_number_out
                number_in = new_number_in
            
            # 当前矩阵不为空，则把新数据添加进去
            else: 
                f.write( "输出满足要求的订单后剩下的入机场订单：" + str(number_out)+'\n')
                f.write( "输出满足要求的订单后剩下的出机场订单：" + str(number_in)+'\n')
                new_number_out = len(new_customer_ID_out)
                new_number_in = len(new_customer_ID_in)
                
                # 更新distance_airport, time_airport
                distance_airport_out = distance_airport[0:number_out]
                distance_airport_in = distance_airport[number_out:]
                time_airport_out = time_airport[0:number_out]
                time_airport_in = time_airport[number_out:]
                
                for i in range(0, new_number_out):
                    dis_tmp, time_tmp = driving_time([113.814, 22.623], new_location_out[i])
                    dis_tmp_2, time_tmp_2 = driving_time(new_location_out[i], [113.814, 22.623])
                    
                    distance_airport_out.append([dis_tmp, dis_tmp_2])
                    time_airport_out.append([time_tmp, time_tmp_2])
                    num_of_API_used_tmp += 2 #记录次数
                
                unvalid_orders = [] 
                for i in range(0, new_number_in):
                    dis_tmp, time_tmp = driving_time([113.814, 22.623], new_location_in[i])
                    dis_tmp_2, time_tmp_2 = driving_time(new_location_in[i], [113.814, 22.623])
                    
                    if time_tmp > 6600:
                        unvalid_orders.append(i)
                    
                    distance_airport_in.append([dis_tmp, dis_tmp_2])
                    time_airport_in.append([time_tmp, time_tmp_2])
                    num_of_API_used_tmp += 2 #记录次数
                
                # 到机场的直通行驶时间超过2小时（1小时50分）的 [入机场] 数据，删除
                if len(unvalid_orders)!= 0:
                    unvalid_orders.sort(reverse=True)
                    for i in range(0, len(unvalid_orders)):
                        i_tmp = unvalid_orders[i]
                        new_customer_ID_in.pop(i_tmp)
                        new_time_window_in.pop(i_tmp)
                        new_location_in.pop(i_tmp)
                        
                        distance_airport_in.pop(number_in + i_tmp)
                        time_airport_in.pop(number_in + i_tmp)
                        
                    f.write( "删掉超时订单后的新入机场订单数：" + str(len(new_customer_ID_in)) + '\n')
                    new_number_in = len(new_customer_ID_in)
                
                distance_airport = distance_airport_out + distance_airport_in
                time_airport = time_airport_out + time_airport_in
                
                # customer向量：ID, 时间窗, 行驶时间上限, 地点坐标
                current_customer_out = current_customer[0:number_out]
                current_customer_in = current_customer[number_out:]
                
                for i in range(0, new_number_out):
                    current_customer_out.append([new_customer_ID_out[i], new_time_window_out[i], time_airport_out[number_out + i][0]*1.5, new_location_out[i]])
                
                for i in range(0, new_number_in):
                    current_customer_in.append([new_customer_ID_in[i], new_time_window_in[i], time_airport_in[number_in + i][1]*1.5, new_location_in[i]])
                current_customer = current_customer_out + current_customer_in
                
                # 两个矩阵
                # i为行，j为列
                # 画图有助于理解，矩阵分四大块，添加的部分也是四部分
                n_total = len(current_customer)
                for i in range(0, number_out):
                    
                    for j in range(0, new_number_out):
                        dis_tmp, time_tmp = driving_time(current_customer[i][3], new_location_out[j])
                        distance_matrix[i].insert(number_out + j, dis_tmp)
                        time_matrix[i].insert(number_out + j, time_tmp)
                        num_of_API_used_tmp += 1 #记录次数
                    
                    for j in range(0, new_number_in):
                        dis_tmp, time_tmp = driving_time(current_customer[i][3], new_location_in[j])
                        distance_matrix[i].append(dis_tmp)
                        time_matrix[i].append(time_tmp)
                        num_of_API_used_tmp += 1 #记录次数
                
                for i in range(0, new_number_out):
                    d_tmp = []
                    t_tmp = []
                    
                    for j in range(0, n_total):
                        if j == i + number_out:
                            d_tmp.append(0)
                            t_tmp.append(0)
                        else:
                            dis_tmp, time_tmp = driving_time(new_location_out[i], current_customer[j][3])
                            d_tmp.append(dis_tmp)
                            t_tmp.append(time_tmp)
                            num_of_API_used_tmp += 1 #记录次数
                            
                    distance_matrix.insert(number_out + i, d_tmp)
                    time_matrix.insert(number_out + i, t_tmp)
                
                for i in range(number_out + new_number_out, number_out + new_number_out + number_in):
                    
                    for j in range(0, new_number_out):
                        dis_tmp, time_tmp = driving_time(current_customer[i][3], new_location_out[j])
                        distance_matrix[i].insert(number_out + j, dis_tmp)
                        time_matrix[i].insert(number_out + j, time_tmp)
                        num_of_API_used_tmp += 1 #记录次数
                    
                    for j in range(0, new_number_in):
                        dis_tmp, time_tmp = driving_time(current_customer[i][3], new_location_in[j])
                        distance_matrix[i].append(dis_tmp)
                        time_matrix[i].append(time_tmp)
                        num_of_API_used_tmp += 1 #记录次数
                
                for i in range(0, new_number_in):
                    d_tmp = []
                    t_tmp = []
                    
                    for j in range(0, n_total):
                        if j == i + number_out + new_number_out + number_in:
                            d_tmp.append(0)
                            t_tmp.append(0)
                        else:
                            dis_tmp, time_tmp = driving_time(new_location_in[i], current_customer[j][3])
                            d_tmp.append(dis_tmp)
                            t_tmp.append(time_tmp)
                            num_of_API_used_tmp += 1 #记录次数
                            
                    distance_matrix.append(d_tmp)
                    time_matrix.append(t_tmp)
                    
                number_out += new_number_out
                number_in += new_number_in
                
        else:
            f.write( "没有新订单"+'\n')
            if len(current_customer) == 0:
                if len(current_solution) == 0:
                    f.write( "上一轮没有留下未分配订单"+'\n')
                else:
                    f.write( "上一轮有未分配订单，但发车后已无剩余"+'\n')
            else:
                f.write( "原来的累积入机场订单" + str(number_out)+'\n')
                f.write( "原来的累积出机场订单" + str(number_in)+'\n')
                
                
        num_of_API_used.append(num_of_API_used_tmp)
        end_time_matrix=time.clock()
        f.write( "调用API次数：" + str(num_of_API_used_tmp) +'\n')
        f.write( "形成矩阵所需时间：" + str(end_time_matrix-start_time_matrix) +'\n')
        
        
        """
        ============ 重新算VNS ============
        """      
        current_solution = []
        start_time = []
        # if len(new_customer_ID_out) + len(new_customer_ID_in) == 0:
        if len(current_customer) == 0:
            f.write( "本轮不计算"+'\n')
            nodes_number.append(0)
        else:
            # current_solution = []
            # start_time = []
            f.write( "本轮计算的点数：" + str(len(current_customer))+'\n')
            nodes_number.append(len(current_customer))
            initialSolution = initial_solution(current_customer, distance_matrix, distance_airport, time_matrix, time_airport, number_out)

            current_solution = VNS_calculate(initialSolution, current_customer, distance_matrix, distance_airport, time_matrix, time_airport, number_out)
            
            for i in range(0, len(current_solution)):
                start_time.append(route_start_time(current_solution[i], current_customer, time_matrix, time_airport, number_out))
        """
        # debug - 1
        for i in range(0, len(current_solution)):
            
            # 输出客户ID
            settled_route = ["airport"]
            for j in range(1, len(current_solution[i])-1):
                settled_route.append(current_customer[ current_solution[i][j] ][0])
            settled_route.append("airport")
                
            # 输出时间数据，转换成可读字符串
            this_times, waiting_time = route_time_intervals(current_solution[i], current_customer, time_matrix, time_airport, number_out)
            this_times_2 = []
            for j in range(0, len(this_times)):
                time_tmp = [time.strftime("%H:%M:%S", time.localtime(this_times[j][0] + 1438500000.0)),
                            time.strftime("%H:%M:%S", time.localtime(this_times[j][1] + 1438500000.0))]
                this_times_2.append(time_tmp)
                
            for j in range(0, len(this_times)):
                if this_times[j][1] - this_times[j][0] < max_timeWindow_interval:
                    print "--------出现时间范围小于1分钟的------------"
                    print timestr_1, timestr_2
                    print settled_route
                    print this_times_2
                    # print "检验出发时间：", [time.strftime("%H:%M:%S", time.localtime(start_time[i][0] + 1438500000.0)),
                                            # time.strftime("%H:%M:%S", time.localtime(start_time[i][1] + 1438500000.0))]
                    print "------------------------------------------"
                    break
        """   
        
        end = time.clock()
        CPU_time.append(end-start)
        f.write( "本轮占用CPU时间：" + str(end-start)+'\n' + '\n')
        
    """
    ========================== 循环结束，输出总数据 ======================================
    """
    # 总车次数，总行驶距离，平均每车次行驶距离，车队总平均的全程平均乘客数
    # 平均每轮循环所需时间，总时间
    # 总乘客点数，距离函数（API)总调用次数
    f.write( "=============计算结束==============" + '\n')
    f.write( "剩余未处理订单：" + str(current_customer) + '\n')
    
    f.write( "通知时间比较紧张的情况：" + str(check_bug) + '\n')
    f.write( "错位时长（分钟）：" + str(check_bug_2) + '\n')
    
    f.write( "总乘客数：" + str(sum(customer_num_served)) + "  总车次数：" + str(number_of_vehicles) + "  平均每车乘客数：" + str(float(sum(customer_num_served))/number_of_vehicles) + '\n')
    
    f.write( "总行驶距离：" + str(sum(total_distance)) + "  平均每车行驶距离：" + str(sum(total_distance)/number_of_vehicles) + "  车队总平均的全程平均乘客数：" + str(sum(customer_num_weighted_distance)/sum(total_distance)) + '\n')
    
    f.write( "平均每轮循环所需时间：" + str(sum(CPU_time)/len(CPU_time)) + "  总CPU计算时间：" + str(sum(CPU_time)) + "  调用API/距离计算函数总次数" + str(sum(num_of_API_used)) + '\n')
    
    f.write( "每轮计算的[点数，时间（秒）,调用API次数]：")
    a=[]
    for i in range(0, len(CPU_time)):
        a.append([nodes_number[i], round(CPU_time[i],2), num_of_API_used[i]])
    f.write( str(a) + '\n')
    
    f.close()