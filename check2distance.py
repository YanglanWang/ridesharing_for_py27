import vrp_airport_v1


def check2distance( a ):
    can_insert = 1
    # expected_return_time=0
    time_list = []
    whole_distance = vrp_airport_v1.distance_dictionary['airport' + '_' + a.route_list[0].id]
    time_list.append( whole_distance )
    if len( a.route_list ) == 1:
        whole_distance = whole_distance + vrp_airport_v1.distance_dictionary[a.route_list[k].id + '_' + 'airport']
        time_list.append( whole_distance )
    else:
        while can_insert==1:
            for k in range( 0, len( a.route_list ) - 1 ):
                whole_distance = whole_distance + vrp_airport_v1.distance_dictionary[
                    a.route_list[k].id + '_' + a.route_list[k + 1].id]
                if whole_distance > 2 * vrp_airport_v1.distance_dictionary['airport' + '_' + a.route_list[k].id]:
                    time_list = []
                    can_insert = 0

                else:
                    time_list.append( whole_distance )
                    if k==len(a.route_list)-2:
                        whole_distance = whole_distance + vrp_airport_v1.distance_dictionary[a.route_list[k + 1].id + '_' + 'airport']
                        time_list.append(whole_distance)
    return can_insert, time_list