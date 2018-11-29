# -*- coding: utf-8 -*-
filename= 'test_dictionary'
dist=dict()
with open( filename, 'r' ) as file_to_read:
    # j = 1  # 用于添加用户ID
    while True:
        lines = file_to_read.readline()  # 整行读取数据
        if not lines:
            break
            pass

        # 将整行数据分割处理，如果分割符是空格，括号里就不用传入参数，如果是逗号， 则传入‘，'字符。
        key, value = [ i for i in lines.split( ', ' )]
        dist[key]=float(value[:-1])

print(dist)
