import distance_calculate
import vrp_airport_v1
import numpy as np


class Demand:
    def __init__(self, id, position, service_type, on_time):
        self.id=id
        self.position=position
        self.service_type=service_type
        self.on_time=on_time
        # self.off_time=off_time

    def update_distance_dictionary( self, demands ):
        # distance_dictionary=dict()
        for i in demands:
            key1=self.id+'_'+i.id
            distance1= distance_calculate.manhattan_calculate( self.position, i.position )
            key2=i.id+'_'+self.id
            distance2 = distance_calculate.manhattan_calculate( i.position, self.position )

            vrp_airport_v1.distance_dictionary[key1]=distance1
            vrp_airport_v1.distance_dictionary[key2]=distance2

        key3=self.id+'_'+'airport'
        airport=np.array([113.814, 22.623])
        distance3=distance_calculate.manhattan_calculate(self.position,airport)
        key4='airport'+'_'+self.id
        distance4=distance_calculate.manhattan_calculate(airport,self.position)
        vrp_airport_v1.distance_dictionary[key3]=distance3
        vrp_airport_v1.distance_dictionary[key4]=distance4


class Route:
    def __init__(self, route_id, route_list, drop_time_list):
        self.route_id = route_id
        self.route_list = route_list
        self.drop_time_list = drop_time_list









