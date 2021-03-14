#!/usr/bin/env python

import linuxcnc
import hal

class CncDriver():
    def __init__(self):
        self.cnc_s = linuxcnc.stat()
        self.cnc_c = linuxcnc.command()

    def ok_for_mdi(self):
        self.cnc_s.poll()
        return not self.cnc_s.estop and self.cnc_s.enabled and (self.cnc_s.homed.count(1) == self.cnc_s.joints) and (self.cnc_s.interp_state == linuxcnc.INTERP_IDLE)

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

driver = CncDriver()

S = driver.find_hole_center()
print(S)