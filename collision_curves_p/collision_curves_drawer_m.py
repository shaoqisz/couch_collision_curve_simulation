import ipywidgets as widgets
from ipywidgets import interact, interact_manual
import numpy as np
import pandas as pd
import pylab as pl
import collision_curves_p.collision_curves_generator_m as ccg


class collision_curves_drawer():
    def __init__(self, p1_pos, p2_pos, p3_pos, bore_down_limit, iso_center, generator, has_motorized_sub_pallet):
        self.m_p3_pos                        = p3_pos
        self.m_p2_pos                        = p2_pos
        self.m_p1_pos                        = p1_pos
        self.m_p1_p2_dis                     = self.m_p2_pos - self.m_p1_pos
        self.m_bore_down_limit               = bore_down_limit
        self.m_iso_center                    = iso_center
        self.m_generator                     = generator
        self.m_has_motorized_sub_pallet      = has_motorized_sub_pallet

    m_colormap                      = ['green', 'blue', 'orange', 'cyan', 'olive', 'purple', 'brown']
    m_last_sp_encoder_pos           = 0
     # default values, feel free to change
    m_default_vertical              = 400
    m_default_curve_size            = 2
    m_default_angle                 = 10

    def draw_curve(self, df, color, alpha=1.0):
        pl.plot(df['Angle'], df['Down'], label=f'{df.name} down', color=color, alpha=alpha) # x=angle, y=down
        pl.plot(df['Angle'], df['Upper'], label=f'{df.name} upper', color=color, alpha=alpha) # x=angle, y=upper
        pl.xticks(np.arange(-300, 300, 50)) 
        pl.yticks(np.arange(-25, 450, 25))
        pl.xlabel('Angle(1/10 Degrees)')
        pl.ylabel('Vertical(mm)')
        pl.ylim(450, -25)
        pl.grid(True)
        pl.legend(loc='lower left')
        
    def mark_point(self, x, y, color='red', marker='.', markerfacecolor='none', offset=[0, 0], description=''):
        pl.plot(x, y, color=color, marker=marker, markerfacecolor=markerfacecolor)
        pl.text(x + offset[0], y + offset[1], f'({x:.0f}, {y:.1f}) {description}', color=color)
        
    def mark_point_at_angle(self, df, angle, color='red', alpha=1.0, marker='.', markerfacecolor='none', offset=[0, 0], description=''):
        y = df.loc[df['Angle'] >= angle][0:1]['Down'].iat[0]
        x = angle
        pl.plot(x, y, color=color, alpha=alpha, marker=marker, markerfacecolor=markerfacecolor)
        pl.text(x + offset[0], y + offset[1], f'({x:.0f}, {y:.0f}){description}', color=color, alpha=alpha)
        return [x, y]

    def pickUpContinuous(self, series, key_value, interval):    
        last_value = series.iat[0] - interval
        start = series.first_valid_index()
        end = series.last_valid_index()

        found = False
        for index, value in series.items():
            if value == key_value:
                found = True
            if abs(value - last_value) != interval:
                if found == True:
                    break
                start = index
            last_value = value
            end = index
        
        return series.loc[start:end]

    def mark_point_at_vertical(self, df, vertical, color='red', alpha=1.0, marker='.', markerfacecolor='none', offset=[0, 0], description=''):
        [valid, x1, x2, y] = self.get_point_at_vertical(df, vertical)
            
        if valid == True:
            pl.plot(x1, y, color=color, alpha=alpha, marker=marker, markerfacecolor=markerfacecolor)
            pl.text(x1 + offset[0], y + offset[1], f'({x1:.0f}, {y:.0f}){description}', color=color, alpha=alpha)

            pl.plot(x2, y, color=color, alpha=alpha, marker=marker, markerfacecolor=markerfacecolor)
            pl.text(x2 + offset[0], y + offset[1], f'({x2:.0f}, {y:.0f}){description}', color=color, alpha=alpha)

        return [valid, x1, x2, y]

    def get_point_at_vertical(self, df, vertical):
        segment_down = df.loc[df['Down'] >= vertical]
        segment_upper = df.loc[df['Upper'] <= vertical]

        if len(segment_down) > 0 and len(segment_upper) > 0:
            continuous_segment_down = self.pickUpContinuous(segment_down['Angle'], 0.0, 1.0)
            continuous_segment_upper = self.pickUpContinuous(segment_upper['Angle'], 0.0, 1.0)
            
            x1 = max(continuous_segment_down.iat[0], continuous_segment_upper.iat[0])
            x2 = min(continuous_segment_down.iat[-1], continuous_segment_upper.iat[-1])
            
            y = vertical
            
            return [True, x1, x2, y]

        return [False, 0, 0, 0]

    def mark_point_at_positive_angle_and_at_down(self, df, down, color='red', marker='.', markerfacecolor='none', offset=[0, 0], description=''):
        y= df.loc[df['Angle'] >= 0].loc[df['Down'] >= down][0:1]['Down'].iat[0]
        x = df.loc[df['Angle'] >= 0].loc[df['Down'] >= down][0:1]['Angle'].iat[0]
        pl.plot(x, y,  color=color, marker=marker, markerfacecolor=markerfacecolor)
        pl.text(x + offset[0], y + offset[1], f'({x:.0f}, {y:.0f}){description}', color=color)
        return [x, y]

    def draw_vertical_line(self, x, ymin, ymax, color, alpha, linestyle, text='', textx='', texty=''):
        pl.vlines(x=x, ymin=ymin, ymax=ymax, color=color, alpha=alpha, linestyle=linestyle)
        if len(text) > 0:
            pl.text(textx, texty, text, color=color, alpha=alpha)
        
    def draw_horizontal_line(self, y, xmin, xmax, color, alpha, linestyle, text='', textx='', texty=''):
        pl.hlines(y=y, xmin=xmin, xmax=xmax, color=color, alpha=alpha, linestyle=linestyle)
        if len(text) > 0:
            pl.text(textx, texty, text, color=color, alpha=alpha)

    def is_in_notebook(self):
        import sys
        return 'ipykernel' in sys.modules

    def clear_output(self):
        """
        clear output for both jupyter notebook and the console
        """
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        if self.is_in_notebook():
            from IPython.display import clear_output as clear
            clear()
        
    def printCouchCurve(self, curve_name):
        if curve_name == 'None':
            self.clear_output()
            return
        for curve in self.m_generator.m_interpolated_collision_curves:
            if curve.name == curve_name:
                print(f'{curve_name}')
                print(curve.to_string())

    def printGantryCurve(self, curve_name):
        if curve_name == 'None':
            self.clear_output()
            return
        for curve in self.m_generator.m_interpolated_collision_curves:
            if curve.name == curve_name:
                print(f'{curve_name}')
                for vertical_encoder_pos in range(90, int(self.m_bore_down_limit)+1): # the range was got from the min height to max height from the collision upper and lower curves.
                    v = self.get_point_at_vertical(curve, vertical_encoder_pos+0.7)
                    print(f'{v[1]}, {v[2]}, {v[3]}')
            

    def convert_sp_relative_pos_to_encoder_pos(self, sp_relative_pos):
        return self.m_p2_pos-sp_relative_pos

    def convert_sp_encoder_pos_to_relative_pos(self, sp_encoder_pos):
        return self.m_p2_pos-sp_encoder_pos

    def convert_sp_encoder_pos_to_display_pos(self, sp_encoder_pos):
        return self.m_p3_pos-sp_encoder_pos

    def convert_sp_display_pos_to_relative_pos(self, sp_display_pos):
        return sp_display_pos-(self.m_p3_pos-self.m_p2_pos)

    def convert_vertical_display_pos_to_encoder_pos(self, vertical_display_pos):
        return 650.7-vertical_display_pos

    def set_current_angle_and_draw_all(self, debug_mode, curve_size, motion_window_of_angle, 
                                    bore_down_limit, sub_pallet_settings, 
                                    set_sub_pallet_pos, angle, vertical_display_pos):

        retraction_angle = motion_window_of_angle[0]
        extension_angle = motion_window_of_angle[1]

        self.m_generator.build_collision_curves(curve_size)
        
        # draw-1 horizontal lines
        self.draw_horizontal_line(bore_down_limit, -300, 300, 'purple', 1.0, '--', text=f'bore down limit({bore_down_limit} mm)', textx=80, texty=bore_down_limit+15)
        self.draw_horizontal_line(self.m_iso_center, -300, 300,  'purple', 1.0, '--', text =f'ISO center({self.m_iso_center} mm)', textx=-290, texty=self.m_iso_center-8)
        
        sp_relative_pos = self.m_p1_p2_dis
        if sub_pallet_settings == 'Auto':
            if angle >= extension_angle:
                sp_relative_pos = 0
            elif angle >= retraction_angle:
                sp_relative_pos = self.m_p1_p2_dis - (self.m_p1_p2_dis * (angle - retraction_angle) / (extension_angle - retraction_angle))
            else:
                sp_relative_pos = self.m_p1_p2_dis
        elif sub_pallet_settings == 'Encoder':
            sp_relative_pos = self.convert_sp_encoder_pos_to_relative_pos(set_sub_pallet_pos)
        elif sub_pallet_settings == 'System':
            sp_relative_pos = self.convert_sp_display_pos_to_relative_pos(set_sub_pallet_pos)
        elif sub_pallet_settings == 'P1':
            sp_relative_pos = self.m_p1_p2_dis
        elif sub_pallet_settings == 'P2':
            sp_relative_pos = 0
        elif sub_pallet_settings == 'P3':
            sp_relative_pos = 0-(self.m_p3_pos - self.m_p2_pos)
        
        current_up_limit = 0
        current_down_limit = 0
        vertical_encoder_pos = self.convert_vertical_display_pos_to_encoder_pos(vertical_display_pos)
        # draw-2: collision curves
        curve_names = ['None']
        tolerance = -0.65
        curve_size = len(self.m_generator.m_interpolated_collision_curves)
        step = self.m_p1_p2_dis / (curve_size - 1) 
        high_light_index =  int((self.m_p1_p2_dis - (sp_relative_pos + tolerance)) / step)
        for index in range(len(self.m_generator.m_interpolated_collision_curves)):
            df = self.m_generator.m_interpolated_collision_curves[index]
            curve_names.append(df.name)
            if index == high_light_index:
                current_down_limit = df.loc[df['Angle'] >= angle]['Down'].iat[0]
                current_up_limit = df.loc[df['Angle'] >= angle]['Upper'].iat[0]
                self.draw_curve(df, self.m_colormap[index % len(self.m_colormap)], 1.0)
                if debug_mode is True:
                    self.mark_point_at_vertical(df, vertical_encoder_pos, 'orange', 1.0, '.')
                    self.mark_point_at_angle(df, retraction_angle,'orange', 1.0, '.', offset = [-35, -15])
                    self.mark_point_at_angle(df, extension_angle, 'orange', 1.0, '.', offset = [10, -15])
            else:
                self.draw_curve(df, self.m_colormap[index % len(self.m_colormap)], 0.08)
        
        # draw-3: circle of angle point
        current_down_limit = min(current_down_limit, bore_down_limit)
        
        if vertical_encoder_pos > current_down_limit or vertical_encoder_pos < current_up_limit:
            self.mark_point(angle, vertical_encoder_pos, color='red', marker='o', markerfacecolor='red', offset=[-50, 20], description=' collision!')
        else:
            self.mark_point(angle, vertical_encoder_pos, color='green', marker='o', markerfacecolor='none', offset=[-60, 20]) # description=f', down={current_down_limit:.0f}'

        # draw-4: sp axis
        if self.m_has_motorized_sub_pallet:
            # motion window
            self.draw_vertical_line(retraction_angle, 400, 120, 'blue', 0.75, '--', text ='motion window', textx = retraction_angle-150, texty = 200)
            self.draw_vertical_line(extension_angle, 400, 120,  'blue', 0.75, '--')

            sp_encoder_pos = self.convert_sp_relative_pos_to_encoder_pos(sp_relative_pos)
            sp_display_pos = self.convert_sp_encoder_pos_to_display_pos(sp_encoder_pos)
            icon = ['[', ']']
            sub_pallet_pos_str = ""
            if self.m_last_sp_encoder_pos < sp_encoder_pos:
                icon[0] = '<'
            elif self.m_last_sp_encoder_pos > sp_encoder_pos:
                icon[1] = '>'
            if sp_encoder_pos > self.m_p3_pos:
                sub_pallet_pos_str = f'|-{icon[0]}{icon[1]}- P3={self.m_p3_pos} ---------- P2={self.m_p2_pos} ------------------ P1={self.m_p1_pos} ----|'
            elif self.m_p3_pos == sp_encoder_pos:
                sub_pallet_pos_str = f'|----{icon[0]}P3={self.m_p3_pos}{icon[1]}---------- P2={self.m_p2_pos} ------------------ P1={self.m_p1_pos} ----|'
            elif self.m_p3_pos > sp_encoder_pos and sp_encoder_pos > self.m_p2_pos:
                sub_pallet_pos_str = f'|---- P3={self.m_p3_pos} ----{icon[0]}{icon[1]}---- P2={self.m_p2_pos} ------------------ P1={self.m_p1_pos} ----|'
            elif self.m_p2_pos == sp_encoder_pos:
                sub_pallet_pos_str = f'|---- P3={self.m_p3_pos} ----------{icon[0]}P2={self.m_p2_pos}{icon[1]}------------------ P1={self.m_p1_pos} ----|'
            elif self.m_p2_pos > sp_encoder_pos and sp_encoder_pos > self.m_p1_pos:
                sub_pallet_pos_str = f'|---- P3={self.m_p3_pos} ---------- P2={self.m_p2_pos} --------{icon[0]}{icon[1]}-------- P1={self.m_p1_pos} ----|'
            elif self.m_p1_pos == sp_encoder_pos:
                sub_pallet_pos_str = f'|---- P3={self.m_p3_pos} ---------- P2={self.m_p2_pos} ------------------{icon[0]}P1={self.m_p1_pos}{icon[1]}----|'
            else:
                sub_pallet_pos_str = f'|---- P3={self.m_p3_pos} ---------- P2={self.m_p2_pos} ------------------ P1={self.m_p1_pos} -{icon[0]}{icon[1]}-|'
            
            sub_pallet_pos_str = f'SP Axis: |Out{sub_pallet_pos_str}In|        |Gantry|'

            pl.title(f'Collision Curves for SP @ Encoder={sp_encoder_pos:.0f}mm, System={sp_display_pos:.0f}mm', fontsize=10)
            pl.show()
            print(sub_pallet_pos_str)
            self.m_last_sp_encoder_pos = sp_encoder_pos
        else:
            pl.title(f'Collision Curves', fontsize=10)
            pl.show()

        if debug_mode is True:
            interact(self.printCouchCurve, curve_name = widgets.Select(options=curve_names,
                                                value='None', 
                                                description='Couch Curve:'))

            interact(self.printGantryCurve, curve_name = widgets.Select(options=curve_names,
                                                value='None', 
                                                description='Gantry Curve:'))

    def update_curve_at_p1(self, data, name='sp @ p1'):
        self.g_collision_curve_sp_at_p1 = pd.DataFrame(columns=['Angle', 'Upper','Down'], data=data)
        self.g_collision_curve_sp_at_p1.name = name

    def update_curve_at_p2(self, data, name='sp @ p2'):
        self.g_collision_curve_sp_at_p2 = pd.DataFrame(columns=['Angle', 'Upper','Down'], data=data)
        self.g_collision_curve_sp_at_p2.name = name

    def run(self):
        debug_mode_ui = widgets.Checkbox(value=False, description='Debug Mode:')

        curve_size_ui = widgets.IntSlider(min=2, max=10, step=1, value=self.m_default_curve_size, description="Curve-Size:", disabled=(self.m_has_motorized_sub_pallet == False))
        
        motion_window_of_angle_ui = widgets.SelectionRangeSlider(options= np.arange(0, 110, 10), index=(1, 6), description='M-Window', disabled=(self.m_has_motorized_sub_pallet == False))

        bore_down_limit_ui = widgets.BoundedFloatText(min=250, max=self.m_bore_down_limit+50, step=10, value=self.m_bore_down_limit, description='Bore Down:', disabled=False)

        vertical_ui = widgets.BoundedFloatText(min=0, max=560, step=5, value=self.m_default_vertical, description='Vertical (mm):')

        angle_slider_ui = widgets.BoundedIntText(min=-300, max=300, step=5, value=self.m_default_angle, description="Tilt (10th):")
        # angle_slider_ui.layout.width = '650px'
        
        set_sub_pallet_pos_ui = widgets.BoundedFloatText(min=0-(self.m_p3_pos - self.m_p2_pos), max=self.m_p3_pos+5, step=5, value=15, description="SP Pos (mm):", disabled=(self.m_has_motorized_sub_pallet == False))

        sub_pallet_settings_ui = widgets.ToggleButtons(
            options=['Auto', 'P1', 'P2', 'P3', 'Encoder', 'System'],
            value='Auto' if self.m_has_motorized_sub_pallet == True else 'P1',
            description='Sub Pallet Position Setting Mode:',
            disabled=(self.m_has_motorized_sub_pallet == False),
            button_style='', # 'success', 'info', 'warning', 'danger' or ''
            tooltips=['Auto', 'Lock @P1', 'Lock @P2', 'Lock @P3', 'Manual Set Encoder', 'Manual Set System']
        )
                
        w = interact(self.set_current_angle_and_draw_all, 
            debug_mode = debug_mode_ui,
            curve_size = curve_size_ui,
            motion_window_of_angle = motion_window_of_angle_ui,
            sub_pallet_settings = sub_pallet_settings_ui,
            set_sub_pallet_pos = set_sub_pallet_pos_ui,
            angle = angle_slider_ui,
            vertical_display_pos = vertical_ui,
            bore_down_limit = bore_down_limit_ui)
