from scipy import interpolate
import numpy as np
import pandas as pd

class collision_curves_generator():

    def __init__(self, collision_curve_sp_at_p1_csv_file, collision_curve_sp_at_p2_csv_file):
        self.m_collision_curve_sp_at_p1      = pd.read_csv(collision_curve_sp_at_p1_csv_file) # 'data/p1.csv'
        self.m_collision_curve_sp_at_p1.name = "sp @ p1"
        self.m_collision_curve_sp_at_p2      = pd.read_csv(collision_curve_sp_at_p2_csv_file) # 'data/p2.csv'
        self.m_collision_curve_sp_at_p2.name = "sp @ p2"

    def build_collision_curves(self, curve_size):
        collision_curves = []
        self.m_interpolated_collision_curves = []
        
        # first one
        collision_curves.append(self.m_collision_curve_sp_at_p1)

        if curve_size >= 2:
            # insert segment
            segment_size = curve_size - 2
            if segment_size > 0:
                down_list = self.calculate_segments(segment_size, 'Down')
                upper_list = self.calculate_segments(segment_size, 'Upper')
                for i in range(segment_size):
                    dict = { 'Angle': self.m_collision_curve_sp_at_p1['Angle'],
                            'Upper': upper_list[i],  
                            'Down': down_list[i] }
                    df = pd.DataFrame(dict)
                    df.name = f'segment {i}'
                    collision_curves.append(df)
            # last one
            collision_curves.append(self.m_collision_curve_sp_at_p2)

        # for collision_curve in collision_curves:
        #     print(f'<{collision_curve.name}>')
        #     display(collision_curve)
        #     print('---------------------------')

        for collision_curve in collision_curves:
            interpolated_collision_curve = self.interpolate_collision_curve(collision_curve)
            self.m_interpolated_collision_curves.append(interpolated_collision_curve)    

    # pick one kind: linear, nearest
    def interpolate_collision_curve(self, collision_curve, kind='linear'):
        angle = collision_curve['Angle']
        down = collision_curve['Down']
        upper = collision_curve['Upper']

        # interpolate
        f_down = interpolate.interp1d(angle, down, kind=kind) #f is a function
        f_upper = interpolate.interp1d(angle, upper, kind=kind) #f is a function

        # down 插值数据
        count = len(collision_curve['Angle'])
        first_angle = collision_curve['Angle'][0]
        last_angle = collision_curve['Angle'][count-1]
        angle_interpolate = np.linspace(first_angle, last_angle, last_angle-first_angle+1)
        down_interpolate = f_down(angle_interpolate) 

        # upper 插值数据
        upper_interpolate = f_upper(angle_interpolate) 

        dict = { 'Angle': angle_interpolate,
                'Upper': upper_interpolate,  
                'Down': down_interpolate }

        interpolated_collision_curve = pd.DataFrame(dict)
        interpolated_collision_curve.name = collision_curve.name
        
        # print(f'<{interpolated_collision_curve.name}>')
        # display(interpolated_collision_curve)
        # print('---------------------------')

        return interpolated_collision_curve

    def calculate_segments(self, size, column_name):
        segments = []
        if size > 0:
            count = len(self.m_collision_curve_sp_at_p2[column_name])
            for x in range(count):
                p1 = self.m_collision_curve_sp_at_p1[column_name].iloc[x]
                p2 = self.m_collision_curve_sp_at_p2[column_name].iloc[x]
                step = (p1 - p2) / (size+1)
                segment = []
                element = p1
                for i in range(size):
                    element = element - step
                    segment.append(element)
                segments.append(segment)            
            segments = np.transpose(segments)
        return segments