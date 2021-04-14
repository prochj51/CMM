#!/usr/bin/env python

import linuxcnc
import sys
import hal
import math
import processor
#from qt5_graphics import Lcnc_3dGraphics

class CncDriver():
    def __init__(self,wait_func = None):
        self.inifile = linuxcnc.ini("~/linuxcnc/configs/cmm/CMM/cmm.ini")
        self.cnc_s = linuxcnc.stat()
        self.cnc_c = linuxcnc.command()
        self.cnc_e = linuxcnc.error_channel()
        self.c_feedrate = 400
        self.probe_tip_diam = float(self.inifile.find("TOOLSENSOR", "TIP_DIAMETER")) or  3.0
        self.probe_tip_rad = self.probe_tip_diam/2
        self.z_base = 0
        self.clearance = 3.
        self.overshoot = 3.
        self.cnc_s.poll()
        self.x_hard_min = self.cnc_s.joint[0]["min_position_limit"] 
        self.x_hard_max = self.cnc_s.joint[0]["max_position_limit"] 
        self.y_hard_min = self.cnc_s.joint[1]["min_position_limit"] 
        self.y_hard_max = self.cnc_s.joint[1]["max_position_limit"] 
        self.z_hard_min = self.cnc_s.joint[2]["min_position_limit"] 
        self.z_hard_max = self.cnc_s.joint[2]["max_position_limit"] 
        self.wait_func = wait_func

    def check_state(self):
        self.cnc_c.state(linuxcnc.STATE_ESTOP_RESET)
        self.cnc_c.state(linuxcnc.STATE_ON)
        self.cnc_s.poll()    
        
    def ok_for_mdi(self):
        self.cnc_s.poll()
        return not self.cnc_s.estop and self.cnc_s.enabled and (self.cnc_s.homed.count(1) == self.cnc_s.joints) and (self.cnc_s.interp_state == linuxcnc.INTERP_IDLE)
    
    def set_camera_home(self,x,y,z=20): #370 creality
        self.camera_home = [x,y,z]
        
    def is_moving(self):
        self.cnc_s.poll()
        return any([abs(self.cnc_s.joint[x]['velocity']) > 0. for x in range(3)])

    def read_error_channel(self):
        # error = self.cnc_e.poll()

        # if error:
        #     kind, text = error
        #     if kind in (linuxcnc.NML_ERROR, linuxcnc.OPERATOR_ERROR):
        #         typus = "error"
        #     else:
        #         typus = "info"
        #     print(typus, text)
        pass

    def rotate_xy_system(self, angle):
        cmd = "G10 L2 P0"    
        cmd += ' R{0:f} '.format(angle)
        self.execute_gcode(cmd)
    
    def isclose(self, a, b, rel_tol=1e-09, abs_tol=0.0):
        return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

    def append_coords_to_gcode(self,cmd,x=None, y=None, z=None, feedrate=None):
        if x is not None:
            cmd += 'X{0:f} '.format(x)
        if y is not None:
            cmd += 'Y{0:f} '.format(y)    
        if z is not None:
            cmd += 'Z{0:f} '.format(z)
        
        if feedrate is None:
            feedrate = self.c_feedrate

        cmd += 'f{0:d} '.format(feedrate)
        print('Command,' + cmd)
        return cmd
    
    def execute_gcode(self,cmd): 
        if not self.ok_for_mdi():
            return
        self.cnc_c.mode(linuxcnc.MODE_MDI)
        self.cnc_c.wait_complete()
        

        self.cnc_c.mdi(cmd)
        
        self.cnc_s.poll()
        while self.cnc_s.interp_state != linuxcnc.INTERP_IDLE :
            #if self.error_poll() == -1:
                #return -1
            if self.wait_func is not None:
                    self.wait_func() #Added so other process is not stalled
            else:
                self.cnc_c.wait_complete()
            self.cnc_s.poll()
        self.cnc_c.wait_complete()
    
    def transform_coordinates(self,x,y,phi):
        x_new = x / math.cos(phi) + (y-x*math.tan(phi))*math.sin(phi)
        y_new = (y-x*math.tan(phi))*math.cos(phi)
        return x_new, y_new   

    def probe_down(self):
        self.probe_to(z=self.z_hard_min)

    def recalc_limits(self):
        self.cnc_s.poll()
        phi_deg = self.cnc_s.rotation_xy
        safety = 1
        if self.isclose(phi_deg,0.):
            return self.x_hard_min + safety, self.x_hard_max - safety, self.y_hard_min + safety, self.y_hard_max - safety
        phi = math.radians(phi_deg)
        phi_compl = math.radians(90 - phi_deg)
                
        x,y = self.get_actual_position(mach_coords = True)[:2]
        x_r, y_r = self.transform_coordinates(x,y,phi)
          
        #xmin
        if y_r >= 0:
            x_r_min = y_r/math.tan(phi_compl)
        else:
            x_r_min = abs(y_r)/math.tan(phi)
        
        #xmax
        x_r_max1 = x_r + (self.x_hard_max - x)/math.cos(phi)
        x_r_max2 = x_r + (self.y_hard_max - y)/math.sin(phi)
        x_r_max = x_r_max1 if (x_r_max1 < x_r_max2) else x_r_max2
        
        #ymin
        y_r_min1 = -math.tan(phi)*x_r
        y_r_min2 = y_r - (self.x_hard_max - x)/math.sin(phi)
        y_r_min = y_r_min1 if (y_r_min1 > y_r_min2) else y_r_min2

        #ymax
        y_r_max1 = math.tan(phi_compl)*x_r
        y_r_max2 = y_r + (self.y_hard_max - y)/math.cos(phi_compl)
        y_r_max = y_r_max1 if (y_r_max1 < y_r_max2) else y_r_max2
        
        return x_r_min + safety, x_r_max - safety, y_r_min + safety, y_r_max - safety
        

    def move_to(self,x=None, y=None, z=None, rel = False, feedrate=None):
        if rel:
            cmd = 'G91 G1'
        else:    
            cmd = 'G1'
        
        cmd = self.append_coords_to_gcode(cmd, x = x,y = y, z = z, feedrate=feedrate)
        self.execute_gcode(cmd)

        if rel:
            self.execute_gcode("G90")


    def probe_to(self,x=None, y=None, z=None, feedrate=100):
        cmd = 'G38.3'
        cmd = self.append_coords_to_gcode(cmd, x = x,y = y, z = z, feedrate=feedrate)
        self.execute_gcode(cmd)    

    def probe_away(self,x=None, y=None, z=None, feedrate=100):
        cmd = 'G38.5'
        cmd = self.append_coords_to_gcode(cmd, x = x,y = y, z = z, feedrate=feedrate)
        self.execute_gcode(cmd)


    def get_actual_position(self, mach_coords = False):
        self.cnc_s.poll()
        x = self.cnc_s.actual_position[0]
        y = self.cnc_s.actual_position[1]
        z = self.cnc_s.actual_position[2]

        if not mach_coords and self.cnc_s.rotation_xy != 0:
            x, y = self.transform_coordinates(x,y,math.radians(self.cnc_s.rotation_xy))
        
        return x,y,z

    def get_probed_position(self, mach_coords = False):
        self.cnc_s.poll()
        x = self.cnc_s.probed_position[0]
        y = self.cnc_s.probed_position[1]
        z = self.cnc_s.probed_position[2]

        if not mach_coords and self.cnc_s.rotation_xy != 0:
            x, y = self.transform_coordinates(x,y,math.radians(self.cnc_s.rotation_xy))
        return x,y,z

    def probe_tripped(self):
        self.cnc_s.poll()
        return self.cnc_s.probe_tripped

    def set_camera_scale(self,x0,y0, xscale, yscale):
        self.x0 = x0
        self.y0 = y0
        self.xscale = xscale
        self.yscale = yscale
        print("Scale was set")


    def camera_to_cnc(self,pix_x,pix_y):
        cnc_x = self.xscale*(self.x0 - pix_x)
        cnc_y = self.yscale*(pix_y - self.y0)
        return cnc_x, cnc_y
    
    def cnc_to_camera(self,cnc_x,cnc_y):
        pix_x = self.x0 - (cnc_x/self.xscale)
        pix_y = self.y0 + (cnc_y/self.yscale)
        return int(pix_x), int(pix_y)

    #go to z_base
    #get the angle gamma_x = atan(x,height_z),gamma_y = atan(y,height_z)
    #G38.2 X#x Y#y Z#min_limit
    #given pixel coordinates
    def probe_in_camera_z_perspective(self,x,y):
        x,y = self.camera_to_cnc(x,y)
        
        x_c = self.camera_home[0]
        y_c = self.camera_home[1]
        z_c = self.camera_home[2]
        
        camera_heigth = z_c - self.z_hard_min
        z_diff = z_c - self.z_base
        
        kx = (x-x_c)/camera_heigth
        ky = (y-y_c)/camera_heigth
        x0 = x_c + kx*z_diff
        y0 = y_c + ky*z_diff
        
        #move to z_base        
        self.move_to(z=self.z_base)
        self.move_to(x=x0,y=y0)
        self.probe_to(x=x,y=y,z=self.z_hard_min)

    def get_opposite_direction(self,dir):
        if dir == 'xminus': 
            return 'xplus'       
        elif dir == 'xplus':
            return 'xminus'
        elif dir == 'yminus':
            return 'yplus'   
        elif dir == 'yplus':
            return 'yminus'    
        elif dir == 'zminus':
            return 'zplus'    
        elif dir == 'zplus':
            return 'zminus'    
        else:
            raise Exception("Wrong Input")

    def find_rising_edge(self,dir):
        self.cnc_s.poll() 
        x_min, x_max, y_min, y_max = self.recalc_limits()
        cl = self.clearance
        if dir == 'xminus': 
            self.probe_to(x = x_min)
            clearance_vec = [cl, 0, 0]      
        elif dir == 'xplus': 
            self.probe_to(x = x_max)
            clearance_vec = [-cl, 0, 0]      
        elif dir == 'yminus':
            self.probe_to(y = y_min)    
            clearance_vec = [0, cl, 0]      
        elif dir == 'yplus':
            self.probe_to(y = y_max)
            clearance_vec = [0, -cl, 0]      
        else:
            raise Exception("Wrong Input")
        dir_opp = self.get_opposite_direction(dir)   
        self.cnc_s.poll()

        #move bit back
        self.move_to(x=clearance_vec[0], y=clearance_vec[1], z=clearance_vec[2], rel = True)

        return self.get_probed_position()[:2]

    def find_falling_edge(self,dir,jump=2):
        jump_x = 0.
        jump_y = 0.
        if dir == 'xminus': 
            jump_x = -jump       
        elif dir == 'xplus':
            jump_x = jump
        elif dir == 'yminus':
            jump_y = -jump    
        elif dir == 'yplus':
            jump_y = jump    
        else:
            raise Exception("Wrong Input")      

        self.cnc_s.poll()        
        self.probe_to(z=self.z_hard_min)
        x0,y0,z0 = self.get_probed_position()
        
        probe_success = True
        indx = 1
        while probe_success:
            self.move_to(z = (z0+self.clearance))
            self.move_to(x = (x0+indx*jump_x),y = (y0+indx*jump_y))
            
            self.probe_to(z = (z0 - self.overshoot))
            self.cnc_s.poll()
            probe_success = self.cnc_s.probe_tripped
            indx = indx + 1

        dir_opp = self.get_opposite_direction(dir)
        x, y, z = self.find_rising_edge(dir_opp)
        self.move_to(x = (x0+indx*jump_x),y = (y0+indx*jump_y))
        self.move_to(z = (z0+self.clearance))
        
        return x,y,z0

    def find_center_between_points(self, dir1, dir2, pos):
        self.find_rising_edge(dir1)
        probe_max = self.cnc_s.probed_position[pos]
        self.find_rising_edge(dir2)
        probe_min = self.cnc_s.probed_position[pos]
        return (probe_max+probe_min)/2

  
    def find_inner_circle_center(self):
        self.cnc_s.poll()
        x0,y0 = self.get_actual_position()[:2]
        x_plus = self.find_rising_edge("xplus")[0]
        self.move_to(x=x0)
        x_minus = self.find_rising_edge("xminus")[0]        
        x_center = (x_plus+x_minus)/2        
        self.move_to(x=x_center)
        y_plus  = self.find_rising_edge("yplus")[1]
        self.move_to(y=y0)
        y_minus = self.find_rising_edge("yminus")[1]
        y_center = (y_plus+y_minus)/2 
        self.move_to(y=y_center)
        
        return x_center,y_center



    #probe z to get reference
    #if estimated radius was given, search rising edges
    #else search falling edges

    def find_outer_circle_center(self,estimated_radius = None):
        self.cnc_s.poll()
        x0 = self.get_actual_position()[0]
        x_plus = self.find_falling_edge("xplus")[0]
        self.move_to(x=x0)
        x_minus = self.find_falling_edge("xminus")[0]
        x_center = x_plus+x_minus/2
        self.move_to(x=x_center)
        y_plus  = self.find_falling_edge("yplus")[1]
        y_minus = self.find_falling_edge("yminus")[1]
        y_center = y_plus+y_minus/2 
        self.move_to(x=y_center)
        
        return x_center,y_center

        

    #probe in initial direction
    #go little bit back
    #probe again near first probing
    #get the angle from last two probings
    #rotate coordinate system
    #probe in opposite direction
    #go between those points
    #probe in perpendicular directio
    def find_inner_rectangle_center(self):
        pt0 = self.find_rising_edge("yplus")[:2]
        x0,y0 = self.get_actual_position()[:2]
        jump = 2
        self.move_to(x = (x0 + jump))
        pt1 = self.find_rising_edge("yplus")[:2]
        phi = processor.get_angle(pt0,pt1)
        phi_deg = math.degrees(phi)
        self.rotate_xy_system(phi_deg)

        return self.find_inner_circle_center()

    def scan_xy(self, x_start, x_end, y_start, y_end, step_x = 10, step_y = 10):
        z_min = self.z_hard_min
        z_max = self.z_base
        o_code = "o<smartprobe> call [{}] [{}] [{}] [{}] [{}] [{}] [{}] [{}]" \
        .format(x_start,x_end,y_start,y_end,step_x,step_y, z_max, z_min)
        print(o_code)
        self.execute_gcode(o_code)   

    def scan_xy_line(self, pt0, pt1, step = 2, datalog = None):
        x0 = pt0[0]
        y0 = pt0[1]
        x1 = pt1[0]
        y1 = pt1[1]

        dx = x1 - x0
        dy = y1 - y0
        rev = True if dy > dx else False 
        if rev:
            dx, dy = processor.reverse(dx,dy)
            x0, y0 = processor.reverse(x0,y0)
            x1, y1 = processor.reverse(x1,y1)
            
        k = float(dy)/float(dx)
        q = y0 - k*x0
        step_x = math.sqrt(float(step**2)/float(k**2+1))
        
        x = x0
        print(rev, k, q)
        while abs(x - x1) > step :
            y = k*x + q
            x_m = y if rev else x
            y_m = x if rev else y
            self.move_to(x=x_m,y=y_m)
            self.probe_down()
            p_x, p_y, p_z = self.get_probed_position()
            if datalog:
                datalog.logProbe(p_x, p_y, p_z)
            self.move_to(z = p_z + 3)
            x = x + step_x

        #print(y0,y_next, y_next2)   
        #print(step_x)  

    def scan_xy(self, datalog = None):
        incr_x = 2
        incr_y = 2
        x_min = 10
        x_max = 50
        y_min = 10
        y_max = 50
        x_count = math.floor(x_max - x_min)/incr_x + 1
        y_count = math.floor(y_max - y_min)/incr_y + 1
        z_min = self.z_hard_min
        z_max = self.z_base
        ind_x = 0
        ind_y = 0

        while ind_y < y_count:
            ind_x  = 0
            self.move_to(y = (y_min + incr_y * ind_y) )

            while ind_x < x_count:
                if self.isclose(y_count - math.floor(y_count),0):
                    x_m = x_min + incr_x*ind_x
                else:    
                    x_m = x_min + incr_x*(x_count - ind_x - 1)
                probe_tripped = 1
                while probe_tripped:
                    self.probe_away(z = z_max)
                    self.probe_to(x = x_m)
                    probe_tripped = self.probe_tripped()

                self.probe_to(z = z_min)
                self.probe_away(z = z_max,feedrate=50)

                #log value
                x_p, y_p, z_p = self.get_probed_position()
                if datalog:
                    datalog.log(x_p,y_p,z_p)

                ind_x = ind_x + 1

            self.move_to(z = z_max)
            ind_y = ind_y + 1    
            
    def scan_circumference(self,direction = -1):
        cnt_max = 600
        cnt = 0
        incr = 2
        state = 0 # 0 1 2 3
        retract = 1
        #direction = -1 #1 = from left, +1 = from right

        if direction == -1:
            self.find_rising_edge("xplus")
        elif direction == 1:
            self.find_rising_edge("xminus")
        else:
            print("Wrong input")
            return
        x0,y0 = self.get_probed_position()[:2]
        while cnt < cnt_max :
            #Check for state overflow
            if state < 0:
                state = 3
            elif state > 3:
                state = 0    

            if state == 0:
                print(state)
                x_m = self.get_actual_position()[0] - direction*2*incr
                self.probe_to(x=x_m)

                # if probe was tripped, change probe direction
                if self.probe_tripped() == 0:
                    state = state - direction
                    
                #else just rectract and continue
                else:
                    #retract
                    x_m = self.get_actual_position()[0] + direction*5*incr
                    self.probe_away(x = x_m)
                    x_m = self.get_actual_position()[0] + direction*retract
                    self.move_to(x = x_m)
                    
                    #move in y
                    y_m = self.get_actual_position()[1] + incr
                    self.probe_to(y = y_m) 
                    if self.probe_tripped() == 1:
                        state = state + direction
                        self.probe_away(y = self.y_hard_min)
                        y_m = self.get_actual_position[1] - retract
                        self.move_to(y = y_m)


            elif state == 1:
                print(state)

                y_m = self.get_actual_position()[1] + direction*2*incr
                self.probe_to(y=y_m)

                # if probe was tripped, change probe direction
                if self.probe_tripped() == 0:
                    state = state - direction
                #else just rectract and continue
                else:
                    #retract
                    y_m = self.get_actual_position()[1] - direction*5*incr
                    self.probe_away(y = y_m)
                    y_m = self.get_actual_position()[1] - direction*retract
                    self.move_to(y = y_m)

                    #move in x
                    x_m = self.get_actual_position()[0] + incr
                    self.probe_to(x = x_m) 
                    if self.probe_tripped() == 1:
                        state = state + direction
                        self.probe_away(x = self.x_hard_min)
                        x_m = self.get_actual_position()[0] - retract
                        self.move_to(x = x_m)

            
            elif state == 2:
                print(state)

                x_m = self.get_actual_position()[0] + direction*2*incr
                self.probe_to(x=x_m)

                # if probe was tripped, change probe direction
                if self.probe_tripped() == 0:
                    state = state - direction
                #else just rectract and continue
                else:
                    #retract
                    x_m = self.get_actual_position()[0] - direction*5*incr
                    self.probe_away(x = x_m)
                    x_m = self.get_actual_position()[0] - direction*retract
                    self.move_to(x = x_m)

                    #move in y
                    y_m = self.get_actual_position()[1] - incr
                    self.probe_to(y = y_m) 
                    if self.probe_tripped() == 1:
                        state = state + direction
                        self.probe_away(y = self.y_hard_max)
                        y_m = self.get_actual_position()[1] + retract
                        self.move_to(y = y_m)
            
            else:
                print(state)

                y_m = self.get_actual_position()[1] - direction*2*incr
                self.probe_to(y=y_m)

                # if probe was tripped, change probe direction
                if self.probe_tripped() == 0:
                    state = state - direction
                #else just rectract and continue
                else:
                    #retract
                    y_m = self.get_actual_position()[1] + direction*5*incr
                    self.probe_away(y = y_m)
                    y_m = self.get_actual_position()[1] + direction*retract
                    self.move_to(y = y_m)

                    #move in x
                    x_m = self.get_actual_position()[0] - incr
                    self.probe_to(x = x_m) 
                    if self.probe_tripped() == 1:
                        state = state + direction
                        self.probe_away(x = self.x_hard_min)
                        x_m = self.get_actual_position()[0] + retract
                        self.move_to(x = x_m)

            cnt = cnt + 1

            x_diff = abs(x0 - self.get_actual_position()[0])
            y_diff = abs(y0 - self.get_actual_position()[1]) 

            if x_diff < incr and y_diff < incr and cnt > 2:
                break


        print("Ended")        
    # def scan_helper(self, m_dir = 'y', p_dir = 'x'):
        
    #     x_p = self.get_actual_position[0] - direction*2*incr
    #     self.probe_to(x=x_p)

    #     # if probe was tripped, change probe direction
    #     if self.probe_tripped() == 0:
    #         state = state - direction
    #     #else just rectract and continue
    #     else:
    #         #retract
    #         x_m = self.get_actual_position[0] + direction*5*incr
    #         self.probe_away(x = x_m)
    #         x_m = self.get_actual_position[0] + direction*retract
    #         self.move_to(x = x_m)

    #         #move in y
    #         y_m = self.get_actual_position[1] + incr
    #         self.probe_to(y = y_m) 
    #         if self.probe_tripped() == 1:
    #             state = state + direction
    #             self.probe_away(y = self.y_hard_min)
    #             y_m = self.get_actual_position[1] - retract

#Just for testing
def main():
    c = CncDriver()
    c.scan_circumference(1)

if __name__ == "__main__":
    main()