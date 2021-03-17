#!/usr/bin/env python

import linuxcnc
import hal

class CncDriver():
    def __init__(self):
        self.cnc_s = linuxcnc.stat()
        self.cnc_c = linuxcnc.command()
        self.c_feedrate = 400

    def ok_for_mdi(self):
        self.cnc_s.poll()
        return not self.cnc_s.estop and self.cnc_s.enabled and (self.cnc_s.homed.count(1) == self.cnc_s.joints) and (self.cnc_s.interp_state == linuxcnc.INTERP_IDLE)


    def move_to(self,x=None, y=None, z=None, feedrate=None):
        if not self.ok_for_mdi():
            return
        self.cnc_c.mode(linuxcnc.MODE_MDI)
        self.cnc_c.wait_complete()
        
        if feedrate is None:
            feedrate = self.c_feedrate

        # cmd = 'G1 G54 X{0:f} Y{1:f} Z{2:f} f5'.format(x, y, z)
        cmd = 'G1 G53'.format(x, y)
        if x:
            cmd += 'X{0:f} '.format(x)
        if y:
            cmd += 'Y{0:f} '.format(y)    
        if z:
            cmd += 'Z{0:f} '.format(z)
        cmd += 'f{0:d} '.format(feedrate)
        print('Command,' + cmd)

        self.cnc_c.mdi(cmd)
        
        self.cnc_s.poll()
        while self.cnc_s.interp_state != linuxcnc.INTERP_IDLE :
            #if self.error_poll() == -1:
                #return -1
            self.cnc_c.wait_complete()
            self.cnc_s.poll()
        self.cnc_c.wait_complete()

    def gcode(self, s, data = None):
        if self.ok_for_mdi():
            self.cnc_c.mode(linuxcnc.MODE_MDI)
            self.cnc_c.wait_complete() # wait until mode switch executed
        else:
            return -1

        for l in s.split("\n"):
            if "G1" in l :
                l+= " F#<_ini[TOOLSENSOR]RAPID_SPEED>"
            self.cnc_c.mdi( l )
            self.cnc_c.wait_complete()
            #if self.error_poll() == -1:
                #return -1
        return 0

    def ocode(self, s, data = None):
        if self.ok_for_mdi():
            self.cnc_c.mode(linuxcnc.MODE_MDI)
            self.cnc_c.wait_complete() # wait until mode switch executed
        else:
            return -1

        self.cnc_c.mdi(s)
        self.cnc_s.poll()
        while self.cnc_s.interp_state != linuxcnc.INTERP_IDLE :
            #if self.error_poll() == -1:
                #return -1
            self.cnc_c.wait_complete()
            self.cnc_s.poll()
        self.cnc_c.wait_complete()
        #if self.error_poll() == -1:
            #return -1
        return 0

    def setCameraScale(self,x0,y0, xscale, yscale):
        self.x0 = x0
        self.y0 = y0
        self.xscale = xscale
        self.yscale = yscale

    #dir...xplus, xminus, yplus, yminus
    def probe_dir(self,dir): 
        self.ocode("O<{}> call".format(dir))

    def find_center_between_points(self, dir1, dir2, pos):
        self.probe_dir(dir1)
        probe_max = self.cnc_s.probed_position[pos]
        self.probe_dir(dir2)
        probe_min = self.cnc_s.probed_position[pos]
        return (probe_max+probe_min)/2

    
    
    
    def find_hole_center(self):
        center_x = self.find_center_between_points("xplus","xminus",0)
        print(center_x)
        self.gcode("G1 X{}".format(center_x))
        center_y = self.find_center_between_points("yplus","yminus",1)
        self.gcode("G1 Y{}".format(center_y))
        print(center_y)
        return center_x,center_y
