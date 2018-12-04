if (len( whole_route ) == 0) or whole_route[0] == None:
    # key = 'airport' + '_' + customer_out_calculating[i].id
    route_list_tmp = []
    route_list_tmp.append( customer_out_calculating[0] )
    time_list = []
    if 'airport' + '_' + customer_out_calculating[0].id not in distance_dictionary.keys():
        distance_dictionary = customer_out_calculating[0].update_distance_dictionary( airport, distance_dictionary )

    # distance_dictionary['airport' + '_' + customer_out_calculating[0].id]
    expected_drop_time0 = distance_dictionary['airport' + '_' + customer_out_calculating[0].id]
    time_list.append( expected_drop_time0 )
    expected_drop_time0 = expected_drop_time0 + distance_dictionary[customer_out_calculating[0].id + '_' + 'airport']
    time_list.append( expected_drop_time0 )

    route_tmp = someclass.Route( None, route_list_tmp, time_list )
    route_tmp0 = []
    route_tmp0.append( route_tmp )
    whole_route[0] = route_tmp0
    # customer_out_calculated_route_id = customer_out_calculated_route_id + 1
    # customer_out_calculated.append( customer_out_calculated_route_id, route )
else:
    for a in whole_route[0]:  # 不同的线路
        exceed, distance_dictionary = check_capacity( a, distance_dictionary )
        if exceed == 0:
            for j in range( 0, len( a.route_list ) + 1 ):
                if j == 0:
                    if 'airport' + '_' + customer_out_calculating[i].id not in distance_dictionary.keys():
                        distance_dictionary = customer_out_calculating[i].update_distance_dictionary( airport,
                                                                                                      distance_dictionary )
                    if customer_out_calculating[i].id + '_' + a.route_list[0].id not in distance_dictionary.keys():
                        distance_dictionary = customer_out_calculating[i].update_distance_dictionary( a.route_list[0],
                                                                                                      distance_dictionary )
                    if 'airport' + '_' + a.route_list[0].id not in distance_dictionary.keys():
                        distance_dictionary = airport.update_distance_dictionary( a.route_list[0], distance_dictionary )

                    distance_increase = distance_dictionary['airport' + '_' + customer_out_calculating[i].id] + \
                                        distance_dictionary[customer_out_calculating[i].id + '_' + a.route_list[0].id] - \
                                        distance_dictionary['airport' + '_' + a.route_list[0].id]
                if j == len( a.route_list ):
                    if a.route_list[-1].id + '_' + customer_out_calculating[i].id not in distance_dictionary.keys():
                        distance_dictionary = a.route_list[-1].update_distance_dictionary(
                            customer_out_calculating[i], distance_dictionary )
                    if customer_out_calculating[i].id + '_' + 'airport' not in distance_dictionary.keys():
                        distance_dictionary = customer_out_calculating[i].update_distance_dictionary( airport,
                                                                                                      distance_dictionary )
                    if a.route_list[-1].id + '_' + 'airport' not in distance_dictionary.keys():
                        distance_dictionary = a.route_list[-1].update_distance_dictionary( airport,
                                                                                           distance_dictionary )
