#!/usr/bin/env python
import cv2
import numpy as np 
import math
import common
import camera
from common import next_frame
from enum import Enum
import sys
from PyQt5 import QtCore

c_label_font = cv2.FONT_HERSHEY_SIMPLEX
c_label_color = (0, 0, 255)
c_label_s = 1
c_label_line_type = cv2.LINE_8
c_demo_mode = False

c_line_color = (0, 200, 0)
c_path_color = (200, 200, 64)
c_line_s = 2
c_crop_rect = None

partialDraw = False # true if mouse is pressed
pt1_x, pt1_y = None, None
mode = 0

layer = 0
layers = []
yellow = (0, 255, 255)
orange = (0,145,255)
blue = (255,0,0)
green = (0,255,0)
black = (0,0,0)

colors = [yellow,black,orange,blue,green]
eventFlag = 0
class States(Enum):
    Setup = 5
    Select = 10
    AutomaticSearch = 20
    ManualSearch = 25
    StandardProbe = 30
    CompleteScan = 50
    LocalScan = 55

def line_length(pt1, pt2):
    delta_x = pt2[0] - pt1[0]
    delta_y = pt2[1] - pt1[1]
    return math.sqrt(delta_x ** 2 + delta_y ** 2)


def object_drawing(event,x,y,flags,param):
    global pt1_x,pt1_y, partialDraw
    if event==cv2.EVENT_LBUTTONDOWN:
        updateImage.moving = False
        if (pt1_x is not None) or (pt1_y is not None):
            mask = layers[layer]
            if mode == 0:
                cv2.rectangle(mask,(pt1_x,pt1_y),(x,y),color=(255,255,255),thickness=-1)
            elif mode == 1:
                cv2.circle(mask,(pt1_x,pt1_y),int(math.sqrt((pt1_x-x)**2 + (pt1_y-y)**2)),color=(255,255,255),thickness=-1)
            elif mode == 2:
                cv2.line(mask,(pt1_x,pt1_y),(x,y),color=(255,255,255),thickness=3)
            pt1_x , pt1_y = None , None
            partialDraw = False
        else:    
            pt1_x,pt1_y=x,y
            partialDraw = True
        
    
    elif event==cv2.EVENT_MOUSEMOVE:
        if (pt1_x is not None) or (pt1_y is not None):
            updateImage.moving = True
            updateImage.img = updateImage.final_pic.copy()
            col = colors[layer]
            if mode == 0:
                cv2.rectangle(updateImage.img,(pt1_x,pt1_y),(x,y),color=col, thickness=-1)
            elif mode == 1:
                cv2.circle(updateImage.img,(pt1_x,pt1_y),int(math.sqrt((pt1_x-x)**2 + (pt1_y-y)**2)),color=col,thickness=-1)
            elif mode == 2:
                cv2.line(updateImage.img,(pt1_x,pt1_y),(x,y),color=col,thickness=3)    
        elif partialDraw == True:
            updateImage.img = updateImage.final_pic
            partialDraw == False


def plate_mask(image):
   
    if c_crop_rect is None:
        mask = np.ones(image.shape, dtype=image.dtype) * 255
    else:
        off = 10
        pt1 = round_pt(add_pts(c_crop_rect[0], (-off, -off)))
        pt2 = round_pt(add_pts(c_crop_rect[1], (off, off)))
        mask = np.zeros(image.shape, dtype=image.dtype)
        cv2.rectangle(mask, pt1, pt2, (255, 255, 255), -1)

    return mask

def object_drawing_qt(event,x,y):
    global pt1_x,pt1_y, partialDraw
    if event.type() == QtCore.QEvent.MouseButtonPress:
        updateImage.moving = False
        if (pt1_x is not None) or (pt1_y is not None):
            mask = layers[layer]
            if mode == 0:
                cv2.rectangle(mask,(pt1_x,pt1_y),(x,y),color=(255,255,255),thickness=-1)
            elif mode == 1:
                cv2.circle(mask,(pt1_x,pt1_y),int(math.sqrt((pt1_x-x)**2 + (pt1_y-y)**2)),color=(255,255,255),thickness=-1)
            elif mode == 2:
                cv2.line(mask,(pt1_x,pt1_y),(x,y),color=(255,255,255),thickness=3)
            pt1_x , pt1_y = None , None
            partialDraw = False
        else:    
            pt1_x,pt1_y=x,y
            partialDraw = True
        
    
    elif event.type() == QtCore.QEvent.MouseMove:
        if (pt1_x is not None) or (pt1_y is not None):
            updateImage.moving = True
            updateImage.img = updateImage.final_pic.copy()
            col = colors[layer]
            if mode == 0:
                cv2.rectangle(updateImage.img,(pt1_x,pt1_y),(x,y),color=col, thickness=-1)
            elif mode == 1:
                cv2.circle(updateImage.img,(pt1_x,pt1_y),int(math.sqrt((pt1_x-x)**2 + (pt1_y-y)**2)),color=col,thickness=-1)
            elif mode == 2:
                cv2.line(updateImage.img,(pt1_x,pt1_y),(x,y),color=col,thickness=3)    
        elif partialDraw == True:
            updateImage.img = updateImage.final_pic
            partialDraw == False


def draw_crosshairs(img, pt, off, c, thickness):
    cv2.line(img, (pt[0] - off, pt[1]), (pt[0] + off, pt[1]), c, thickness=thickness, lineType=cv2.LINE_AA)
    cv2.line(img, (pt[0], pt[1] - off), (pt[0], pt[1] + off), c, thickness=thickness, lineType=cv2.LINE_AA)


def draw_selected_points(img, pts, c=(255, 0, 0), t=1):
    off = 10
    for pt in pts[:-1]:
        draw_crosshairs(img, pt, off, c, t)

    if pts:
    #print(pts)
        pt = pts[-1]
        x, y = pt[0], pt[1]
        off2 = 15
        if off2 < x < img.shape[1] - off2 and off2 < y < img.shape[0] - off2 :
            sub = img[y - off2 // 2:y + off2 // 2, x - off2 // 2:x + off2 // 2, :]
            enlarged = cv2.resize(sub, (off2 * 2, off2 * 2))
            img[y - off2 :y + off2 , x - off2 :x + off2 , :] = enlarged

        draw_crosshairs(img, pt, off, c, t)

mouse_pts = []
mouse_moving = False
mouse_sqr_pts = []
mouse_sqr_pts_done = False


def click_and_crop(event, x, y, flags, param):
    global mouse_pts, mouse_moving
    global mouse_sqr_pts
    global mouse_sqr_pts_done

    # x -= 5
    # y -= 5

    if event == cv2.EVENT_LBUTTONDOWN:
        mouse_pts = [(x, y), None]
        mouse_sqr_pts += [(x, y)]
        if len(mouse_sqr_pts) == 1:
            mouse_sqr_pts += [(x, y)]
        
    elif event == cv2.EVENT_MOUSEMOVE:
        if len(mouse_sqr_pts) == 0:
            mouse_sqr_pts += [(x, y)]
        elif len(mouse_sqr_pts) == 1:
            mouse_sqr_pts[0] = (x, y)
        elif len(mouse_pts) == 2:
            mouse_pts[1] = (x, y)
            mouse_moving = True
            if mouse_sqr_pts:
                mouse_sqr_pts[-1] = (x, y)

    elif event == cv2.EVENT_LBUTTONUP:
        if len(mouse_pts) == 2:
            mouse_pts[1] = (x, y)
            mouse_moving = False

        if not mouse_sqr_pts_done:
            mouse_sqr_pts[-1] = (x, y)

        if len(mouse_sqr_pts) > 4:
            mouse_sqr_pts = mouse_sqr_pts[:4]
            mouse_sqr_pts_done = True

def click_and_crop_qt(event, x, y):
    global mouse_pts, mouse_moving
    global mouse_sqr_pts
    global mouse_sqr_pts_done

    # x -= 5
    # y -= 5

    if event.type() == QtCore.QEvent.MouseButtonPress:
        mouse_pts = [(x, y), None]
        mouse_sqr_pts += [(x, y)]
        if len(mouse_sqr_pts) == 1:
            mouse_sqr_pts += [(x, y)]   
        
    elif event.type() == QtCore.QEvent.MouseMove:
        if len(mouse_sqr_pts) == 0:
            mouse_sqr_pts += [(x, y)]
        elif len(mouse_sqr_pts) == 1:
            mouse_sqr_pts[0] = (x, y)
        elif len(mouse_pts) == 2:
            mouse_pts[1] = (x, y)
            mouse_moving = True
            if mouse_sqr_pts:
                mouse_sqr_pts[-1] = (x, y)

    elif event.type() == QtCore.QEvent.MouseButtonRelease:
        if len(mouse_pts) == 2:
            mouse_pts[1] = (x, y)
            mouse_moving = False

        if not mouse_sqr_pts_done:
            mouse_sqr_pts[-1] = (x, y)

        if len(mouse_sqr_pts) > 4:
            mouse_sqr_pts = mouse_sqr_pts[:4]
            mouse_sqr_pts_done = True

@common.static_vars(img=None,final_pic = None, moving = False,warp_m=None, printHelp = False)
def updateImage(image0):
    #if updateImage.img is None:
        #return image
    global mouse_sqr_pts_done, mouse_sqr_pts

    alpha = 0.4  # Transparency factor.

    # Following line overlays transparent rectangle over the image
    
    rows,cols,channels = image0.shape

    if updateImage.warp_m is not None:
        h, w = image0.shape[:2]
        warped = cv2.warpPerspective(image0, updateImage.warp_m, (w, h))
        image = warped
    else:
        image = image0.copy()


    #get mask
    mask = cv2.cvtColor(layers[layer],cv2.COLOR_BGR2GRAY)
    mask_inv = cv2.bitwise_not(mask)
    #black-out the area of mask in orig_image
    img1_bg = cv2.bitwise_and(image,image,mask = mask_inv)
    #create color layer
    img_2 = np.zeros(image.shape, dtype=np.uint8) 
    col = colors[layer]
    cv2.rectangle(img_2,(0,0),(cols,rows),color=col,thickness=-1)
    # Take masked region from color layer
    img2_fg = cv2.bitwise_and(img_2,img_2,mask = mask)

    updateImage.final_pic = cv2.add(img1_bg,img2_fg)
    updateImage.final_pic = cv2.addWeighted(updateImage.final_pic, alpha, image, 1 - alpha, 0) 


    if mouse_sqr_pts_done:
        #draw_selected_points(updateImage.final_pic, mouse_sqr_pts)

        rct = np.array(mouse_sqr_pts, dtype=np.float32)
        w1 = line_length(mouse_sqr_pts[0], mouse_sqr_pts[1])
        w2 = line_length(mouse_sqr_pts[2], mouse_sqr_pts[3])
        h1 = line_length(mouse_sqr_pts[0], mouse_sqr_pts[3])
        h2 = line_length(mouse_sqr_pts[1], mouse_sqr_pts[2])
        w = max(w1, w2)
        h = max(h1, h2)

        pt1 = mouse_sqr_pts[0]
        dst0 = [pt1, [pt1[0] + w, pt1[1]], [pt1[0] + w, pt1[1] + h], [pt1[0], pt1[1] + h]]
        dst = np.array(dst0, dtype=np.float32)

        updateImage.warp_m = cv2.getPerspectiveTransform(rct, dst)

        pt1, pt2 = dst0[0], dst0[2]
        c_crop_rect = [pt1, pt2]

        mouse_sqr_pts = []
        mouse_sqr_pts_done = False
        #cv2.setMouseCallback('test draw',object_drawing)
        global eventFlag
        eventFlag = 1
        #get_measurement.c_view = 3
        #get_measurement.mouse_op = ''

        #in_alignment = True

    if updateImage.moving:
        alpha = 0.4  # Transparency factor.
        scale = 0.6
            # Following line overlays transparent rectangle over the image
        presentPic = cv2.addWeighted(updateImage.img, alpha, updateImage.final_pic, 1 - alpha, 0) 
        #img_up = np.hstack([presentPic , updateImage.img])
        #img_down = np.hstack([img1_bg, img2_fg])
        #img_all =  np.vstack([img_up, img_down])
        #presentPic = cv2.resize(img_all, None, fx=scale, fy=scale)
    else:
        presentPic = updateImage.final_pic

    
    if not mouse_sqr_pts_done:
        draw_selected_points(presentPic, mouse_sqr_pts)


    if updateImage.printHelp == True:
        def h(i):
            return 200, 130 + i * 35
        
        cv2.putText(presentPic, '{:6s} {}'.format('KEY NUMBERS ', ' - Layer change'), h(-1), c_label_font, c_label_s, c_label_color,thickness=2)
        cv2.putText(presentPic, '{:6s} {}'.format('c ', ' - Draws circle'), h(0), c_label_font, c_label_s, c_label_color,thickness=2)
        cv2.putText(presentPic, '{:6s} {}'.format('r ', ' - Draws rectangle'), h(1), c_label_font, c_label_s, c_label_color,thickness=2)
        cv2.putText(presentPic, '{:6s} {}'.format('e ', ' - Draws line'), h(2), c_label_font, c_label_s, c_label_color,thickness=2)
        cv2.putText(presentPic, '{:6s} {}'.format('h ', ' - Prints help'), h(3), c_label_font, c_label_s, c_label_color,thickness=2)
        cv2.putText(presentPic, '{:6s} {}'.format('q ', ' - Quits intermediate changes'), h(4), c_label_font, c_label_s, c_label_color,thickness=2)
        cv2.putText(presentPic, '{:6s} {}'.format('d ', ' - Deletes mask in current layer'), h(5), c_label_font, c_label_s, c_label_color,thickness=2)
        cv2.putText(presentPic, '{:6s} {}'.format('e ', ' - Draws line'), h(6), c_label_font, c_label_s, c_label_color,thickness=2)
        cv2.putText(presentPic, '{:6s} {}'.format('Esc ', ' - Escape application'), h(7), c_label_font, c_label_s, c_label_color,lineType=c_label_line_type,thickness=2)

    
    cv2.putText(presentPic, '{:6s} {}'.format('Current layer:', layer), (presentPic.shape[1]-300,100), c_label_font, c_label_s, (0,255,0),thickness=2, lineType=c_label_line_type)    

    return presentPic


def next_frame2(video_capture):
    if c_demo_mode:
        fn = 'holes.png'
        # fn_pat = 'tests/z_camera/1280x720/mov_raw_{:06d}.ppm'
        image0 = next_frame(video_capture, fn=fn)
    else:
        image0 = next_frame(video_capture)

    return image0

def camera_setup():
    if c_demo_mode:
        return None

    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        print('camera is not open')
        sys.exit(1)

    camera.set_camera_properties(video_capture, '640x480')
    # camera.list_camera_properties(video_capture)

    return video_capture

def check_layers(orig_img):
    if layer+1 > len(layers):
            
            for indx in range(len(layers),layer+1):
                #add layer mask
                layers.append(np.zeros(orig_img.shape, dtype=np.uint8)) 

def process_key(key):
    global layer,layers,mode
    if key == 27:
        return -1
    elif key == ord('0'):
        layer = 0
    elif key == ord('1'):
        layer = 1
    elif key == ord('2'):
        layer = 2
    elif key == ord('3'):
        layer = 3
    elif key == ord('4'):
        layer = 4      
    elif key == ord('R'):
        mode = 0
    elif key == ord('C'):
        mode = 1     
    elif key == ord('E'):
        mode = 2     
    elif key == ord('Q'):
        pt1_x,pt1_y = None,None
        updateImage.printHelp = False 
        updateImage.warp_m = None 
    elif key == ord('D'):
        layers[layer] = np.zeros(updateImage.final_pic.shape, dtype=np.uint8)   
    elif key == ord('H'):
        updateImage.printHelp = not updateImage.printHelp 
    return 0
def main():
    global mode,pt1_x,pt1_y,layer,layers
    
    video_capture = camera_setup()
    cv2.namedWindow('test draw')
    cv2.setMouseCallback('test draw',click_and_crop)
    while True:
            
        orig_img = next_frame2(video_capture)
        key = cv2.waitKey(5) & 0xFF         
        if process_key(key) == -1:
            break
        check_layers(orig_img)
        
        final_pic = updateImage(orig_img)
        common.draw_fps(final_pic)
        cv2.imshow('test draw',final_pic )

if __name__ == "__main__":
    main()

