import numpy as np

import threading
import os
import cv2
from inputs import get_gamepad


should_exit = False

training_set = '\\sets\\kazuya_all\\'
folder = './sets/kazuya_all/'


is_down = False
is_back = False

blocking_low = False
blocking_mid = False

should_block_low = False
should_block_mid = False
    


def handle_input():
    global should_exit, is_down, is_back, blocking_mid, blocking_low
    while not should_exit:
        events = get_gamepad()
        for event in events:
            match event.code:
                case 'ABS_HAT0X':
                    if event.state == 1:
                        is_back = True
                    else:
                        is_back = False
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
        print(blocking_low, blocking_mid)

def handle_video(move_set, move_id_list):
    for id in move_id_list:
        current_move = move_set[id]
        move_hit_info = current_move[1]

        hit_frame = [int(t[0]) for t in move_hit_info]
        hit_loc = [t[1] for t in move_hit_info]

        success_tot = len(hit_frame)
        successes = 0

        cap = current_move[0]
        # Read until video is completed
        frame_number = 0
        move_stage = 0
        frame_b = []
        while(cap.isOpened()):
            # Capture frame-by-frame
            ret, frame = cap.read()
            if ret == True:
                frame_b = frame
                print(frame_number)
                if frame_number in hit_frame:
                    match hit_loc[move_stage]:
                        case 'm':
                            if blocking_mid:
                                successes =+ 1
                        case 'l':
                            if blocking_low:
                                successes += 1
                    move_stage += 1
                # Display the resulting frame
                cv2.imshow('Frame',frame)
                cv2.waitKey(int(1/30*1000))
                # Press Q on keyboard to  exit
                #while not cv2.waitKey(25) & 0xFF == ord('q'):
                #    pass
                frame_number += 1
            # Break the loop
            else: 
                break
        image = []
        if successes == success_tot:
            image = cv2.rectangle(frame_b, (0,0), (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))), thickness=-1, color=(0,255,0))
        else:
            image = cv2.rectangle(frame_b, (0,0), (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))), thickness=-1, color=(0,0,255))
        frame_max = 30
        frame_number = 0
        while frame_number < frame_max:
                cv2.imshow('Frame', image)
                cv2.waitKey(int(1/30*1000))
                frame_number += 1


        # When everything done, release the video capture object
        cap.release()

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
        for state in move_data[1::]:
            state_info = state.split('-')
            move_frames.append((state_info[0], state_info[1].replace('\n','')))
        moves_processed.append((cap, move_frames))
    return moves_processed

moves_proc = process_set(folder, training_set)

input_thread = threading.Thread(target=handle_input)
video_thread = threading.Thread(target=handle_video, args=(moves_proc, [0,1]))
input_thread.start()
video_thread.start()

  
# Closes all the frames
cv2.destroyAllWindows()

video_thread.join()
input_thread.join()

