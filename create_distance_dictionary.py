# -*- coding: utf-8 -*-
import read_file_py


def create_distance_dictionary():
    distance_dictionary = dict()
    filename_out = '20150803_gaode_offboard.txt'  # 出机场的数据
    filename_in = '20150803_gaode_onboard.txt'  # 入机场的数据
    customer_out, distance_dictionary = read_file_py.read_file2( filename_out, True, distance_dictionary )
    distance_dictionary = read_file_py.read_file3(customer_out, filename_in, False, distance_dictionary )

    g=open('distance_dictionary_euclidean.txt','w')
    for key in distance_dictionary.keys():
        g.write(str(key)+', ' + str(distance_dictionary[key]) + '\n')
    g.close()


create_distance_dictionary()
