import numpy as np

import threading
import os
import random 

import cv2
from inputs import get_gamepad


should_exit = False

training_set = '\\sets\\azucena_all\\'
folder = './sets/azucena_all/'


is_down = False
is_back = False
is_forward = False

blocking_low = False
blocking_mid = False
low_parrying = False    


def handle_input():
    global should_exit, is_down, is_back, is_forward, blocking_mid, blocking_low, low_parrying
    while not should_exit:
        events = get_gamepad()
        for event in events:
            match event.code:
                case 'ABS_HAT0X':
                    if event.state == 1:
                        is_back = True
                        is_forward = False
                    elif event.state == -1:
                        is_back = False
                        is_forward = True
                    else:
                        is_back = False
                        is_forward = False
                case 'ABS_HAT0Y':
                    if event.state == 1:
                        is_down = True
                    else:
                        is_down = False
                case 'BTN_START':
                    should_exit = True
                    print("Exiting")
            #print(event.ev_type, event.code, event.state)
        if is_back and is_down:
            blocking_low = True
        else:
            blocking_low = False
        if is_back and not is_down:
            blocking_mid = True
        else:
            blocking_mid = False
        if is_forward and is_down:
            low_parrying = True
        else:
            low_parrying = False
        print(blocking_low, blocking_mid, low_parrying)

def handle_video(move_set, move_id_list):

    success_rates = {}
    success_totals = {}
    for id in move_id_list:
        current_move = move_set[id]
        move_hit_info = current_move[1]

        hit_frame = [int(t[0]) for t in move_hit_info]
        hit_loc = [t[1] for t in move_hit_info]

        success_tot = len(hit_frame)
        successes = 0

        cap = current_move[0][0]
        framerate = current_move[0][1]
        # Read until video is completed
        frame_number = 0
        move_stage = 0
        while(cap.isOpened()):
            # Capture frame-by-frame
            ret, frame = cap.read()
            if ret == True:
                print(frame_number)
                if frame_number in hit_frame:
                    match hit_loc[move_stage]:
                        case 'm':
                            if blocking_mid:
                                successes += 1
                        case 'l':
                            if blocking_low:
                                successes += 1
                        case 'lp':
                            if low_parrying:
                                 successes += 1
                    move_stage += 1
                # Display the resulting frame
                cv2.imshow('Frame',frame)
                cv2.waitKey(int(1/framerate*1000))
                # Press Q on keyboard to  exit
                #while not cv2.waitKey(25) & 0xFF == ord('q'):
                #    pass
                frame_number += 1
            # Break the loop
            else: 
                break
        frame = np.zeros((int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),3),np.uint8)
        if successes == success_tot:
            cv2.rectangle(frame, (0,0), (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))), thickness=-1, color=(0,255,0))
            if id not in success_rates:
                success_rates[id] = 0
            success_rates[id] += 1
        else:
            cv2.rectangle(frame, (0,0), (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))), thickness=-1, color=(0,0,255))
            if id not in success_rates:
                success_rates[id] = 0

        frame_max = framerate
        frame_number = 0
        while frame_number < frame_max:
                cv2.imshow('Frame', frame)
                cv2.waitKey(int(1/framerate*1000))
                frame_number += 1
        if id not in success_totals:
            success_totals[id] = 0
        success_totals[id] += 1

        # When everything done, release the video capture object
        #cap.release()
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        continue

    rates = {k: float(success_rates[k])/success_totals[k] for k in success_totals}
    #rates=dict(zip(move_set,list(rates.values()))) 
    print(rates)

def process_set(org_folder, video_folder):
    moves_processed = []

    files = os.listdir(org_folder)
    # Filtering only the files.
    files = [f for f in files if os.path.isfile(org_folder+'/'+f)]
    if 'frames.txt' not in files:
        print('You must define a frames.txt file!')
        exit(1)

    #Process frames
    file1 = open(org_folder + 'frames.txt', 'r')
    moves = file1.readlines()
    
    # Strips the newline character
    for move in moves:
        move_data = move.split('_')
        move_video = move_data[0] + '.mp4'
        if move_video not in files:
            print(f'{move_video} not included in files! please include.')
            exit(2)
        moveloc = os.getcwd() + video_folder + move_video
        cap = cv2.VideoCapture(moveloc)
        if (cap.isOpened()== False): 
            print("Error opening video stream or file")
            exit(3)
        move_frames = []
        for state in move_data[2::]:
            state_info = state.split('-')
            move_frames.append((state_info[0], state_info[1].replace('\n','')))
        moves_processed.append(((cap, int(move_data[1])), move_frames))
    return moves_processed




moves_proc = process_set(folder, training_set)

movelist_test = list(np.random.randint(low = 0,high=3,size=20))


input_thread = threading.Thread(target=handle_input)
video_thread = threading.Thread(target=handle_video, args=(moves_proc, movelist_test))
input_thread.start()
video_thread.start()

  
# Closes all the frames
cv2.destroyAllWindows()

video_thread.join()
input_thread.join()

