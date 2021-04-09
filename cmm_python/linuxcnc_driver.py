#!/usr/bin/env python

import linuxcnc
import sys
import hal
import math
import processor

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

    def scan_xy_line(self, pt0, pt1, step = 2):
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
        ### TODO Finish scan routine
        
        x = x0
        print(rev, k, q)
        while abs(x - x1) > step :
            y = k*x + q
            x_m = y if rev else x
            y_m = x if rev else y
            self.move_to(x=x_m,y=y_m)
            self.probe_down()
            p_x, p_y, p_z = self.get_probed_position()
            self.move_to(z = p_z + 3)
            x = x + step_x

        #print(y0,y_next, y_next2)   
        #print(step_x)  



#Just for testing
def main():
    c = CncDriver()
    c.scan_xy_line([10,20],[10,40])

if __name__ == "__main__":
    main()