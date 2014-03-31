'''
preprocessing...
output path

'''
import sys
import cv2
import cv2.cv as cv
import csv
import datetime
import time
import urllib2    
import threading
import os.path
import numpy as np
import itertools
import re
from lib.Frame import *
from lib.Keyword import *
from lib.MovieData import *


OUTPUT_PATH = 'output4/'

HAAR_CASCADE_PATH = "input/haarcascades/haarcascade_frontalface_alt.xml"

class Pthread (threading.Thread):
    
    threadLock = threading.Lock()
    
    def __init__(self, threadID, name, keywordsTime):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.keywordsTime = keywordsTime

    def run(self):
        # Get lock to synchronize threads
        # doing
        print self.name + ' start'
        frameCapture(self.keywordsTime)


def keywordSearch(keywordPath, subtitlePath):
    
    #result time to keywords dictionary
    keywordsTime = {}

    #Read keyword file and store as list
    keywords = []

    with open(keywordPath, "r") as keywordsFile:
        lines = csv.reader(keywordsFile)
        for row in lines:
            keywords.append(row)
   
    #Read movie .srt 
    with open(subtitlePath, "r") as subtitleFile:
        subtitle = subtitleFile.readlines()    

    #search keyword 
    dialog = []
    tmp = []
    
    for line in subtitle:
        
        # is empty line (go to next subtitle)
        if not line.strip():
            for sentence in dialog:
                for word in keywords[0]:
                    #regular expression
                    pattern = word.lower()
                    match = re.search(pattern,sentence.lower())
                    if match:
                        if word.lower == 'amy':
                            print 'AMY'
                        tmp.append(word)
                for word in keywords[1]:
                    pattern = re.compile( word.lower())
                    match = pattern.search(sentence.lower())
                    if match:
                        tmp.append(word)
            if len(tmp) > 0:
               keywordsTime[time] = tmp
            tmp = []
            dialog = []
            continue
        if line[0] == '0':   # time interval
            time = line[:len(line)-3]
        else:
            dialog.append(line)

    for time in keywordsTime:
        print keywordsTime[time],

    return keywordsTime, keywords        



def get_range(dictionary, begin, end):
      return dict(itertools.islice(dictionary.iteritems(), begin, end+1)) 


def frameCapture(keywordsTime):
    
    # load video
    videoInput = cv2.VideoCapture(sys.argv[1])
    keywordID = 1
    faceID = 1

    for key in keywordsTime:
        
        #tansfer time to frame
        startFrame, finishFrame = convertTimeToframe(key)

        #set up startFrame
        framePosition = startFrame - 24*15
        finishFrame += 24 *15

        # detect between startFrame and finishFrame
        while framePosition <= finishFrame: 
            
            if framePosition not in framesDic:
                
                videoInput.set(cv2.cv.CV_CAP_PROP_POS_FRAMES, framePosition)
                flag, frame = videoInput.read()
                mutiPosition = []
                 
                #cv2.imwrite( OUTPUT_PATH + 'img/0.jpg', frame)
                #cv2.imshow('frame', frame)
                mutiPosition = faceDetection(frame, framePosition)
                
                if len(mutiPosition) > 0:
                    print keywordsTime[key]
                    if framePosition in frame:
                        for facePosition in mutiPosition:
                            frames[framePosition].append( Face(facePosition, faceID, framePosition, '', keywordsTime[key], keywordID) )
                            faceID += 1
                    else:
                        frames[framePosition] = []
                        for facePosition in mutiPosition:
                            frames[framePosition].append( Face(facePosition, faceID, framePosition, '', keywordsTime[key], keywordID) )
                            faceID += 1
                
            else:
                if framePosition not in frames and len(framesDic[framePosition]) >= 1: #face number >= 1
                    frames[framePosition] = []
                    for face in framesDic[framePosition]:
                        frames[framePosition].append( Face(face.getPosition(), faceID, framePosition, '', keywordsTime[key], keywordID) )
                        faceID += 1 
            framePosition += 12
        keywordID += 1
    #close video  
    videoInput.release()


def convertTimeToframe(key):
    
    startTime = key[:8]
    tmp = time.strptime(startTime.split(',')[0], '%H:%M:%S' )
    startFrame = int(datetime.timedelta( hours = tmp.tm_hour, minutes = 
                tmp.tm_min, seconds = tmp.tm_sec).total_seconds() * 24)
    
    finishTime = key[17:][:8]
    tmp = time.strptime(finishTime.split(',')[0], '%H:%M:%S' )
    finishFrame = int(datetime.timedelta( hours = tmp.tm_hour, minutes = 
                tmp.tm_min, seconds = tmp.tm_sec).total_seconds() * 24)
    
    return startFrame, finishFrame

def faceDetection(image, framePosition):
    
    faces = []
    
    frame = cv2.CascadeClassifier(HAAR_CASCADE_PATH)
    detected = frame.detectMultiScale(image, 1.1, 4, cv2.cv.CV_HAAR_SCALE_IMAGE, (200, 300) )  #40 150  #25, 160
    
    if len(detected) == 0:
        return []

    detected[:, 2:] += detected[:, :2]
    name = str(framePosition)
    if not os.path.isfile( OUTPUT_PATH + 'img/'+ name + '-1.jpg'):
        outputFaceImage(detected, image, name)
    for rect in detected:
        faces.append(rect)

    return faces


# save the face detection result
def outputFaceImage(rects, img, name):

    print 1
    background = cv2.imread( OUTPUT_PATH + 'img/0.jpg' )
    
    show = img.copy()
    count = 1
    for (x1, y1, x2, y2) in rects:
        cv2.rectangle(show, (x1-10, y1-10), (x2+5, y2+5), (127, 255, 0), 2) 
        saveImage = background.copy()
        face = img[y1:y2, x1:x2]
        saveImage[y1:y2, x1:x2] = face
        cv2.bitwise_and(saveImage, saveImage, face)
        #cv2.imshow("detected", show)
        cv2.imwrite( OUTPUT_PATH + 'img/'+ name + '-' + str(count) + '.jpg', saveImage)
        count +=1

    #cv2.imshow('detected', img)

if __name__=='__main__':
    
    global frames
    global framesDic
    framesDic = {}
    keywordsTime = {}
    keywords = []
    frames = {}
    bipartiteGraph = {}
    
    movieData  = MovieData(OUTPUT_PATH + 'preprocessedData.txt')
   
    faceList, key = movieData.getFaceAndKeyword(0, OUTPUT_PATH)
    for face in  faceList:
        if face.getFrame() not in framesDic:
            framesDic[face.getFrame()] = []
            framesDic[face.getFrame()].append(face)
        else:
            framesDic[face.getFrame()].append(face)

    if len(sys.argv) > 3:
        #print "argv[1] is movie input path for face detection" 
        #keyword search
        print 'keyword search'
        keywordsTime, keywords  = keywordSearch(sys.argv[2], sys.argv[3]) #keyword path, .srt path

        if len(sys.argv) > 2:
            for keyword in keywords[0]:
                bipartiteGraph[keyword] = []
            for keyword in keywords[1]:
                bipartiteGraph[keyword] = []
            
            keywordsTime1 = get_range(keywordsTime, 0, len(keywordsTime)/10)
            keywordsTime2 = get_range(keywordsTime, len(keywordsTime)/10+1, len(keywordsTime)/10*2)
            keywordsTime3 = get_range(keywordsTime, len(keywordsTime)/10*2+1, len(keywordsTime)/10*3)
            keywordsTime4 = get_range(keywordsTime, len(keywordsTime)/10*3+1, len(keywordsTime)/10*4)
            keywordsTime5 = get_range(keywordsTime, len(keywordsTime)/10*4+1, len(keywordsTime)/10*5)
            keywordsTime6 = get_range(keywordsTime, len(keywordsTime)/10*5+1, len(keywordsTime)/10*6)
            keywordsTime7 = get_range(keywordsTime, len(keywordsTime)/10*6+1, len(keywordsTime)/10*7)
            keywordsTime8 = get_range(keywordsTime, len(keywordsTime)/10*7+1, len(keywordsTime)/10*8)
            keywordsTime9 = get_range(keywordsTime, len(keywordsTime)/10*8+1, len(keywordsTime)/10*9)
            keywordsTime10 = get_range(keywordsTime, len(keywordsTime)/10*9+1, len(keywordsTime))

            threads = []
            thread1 = Pthread(1, 'Thread-1', keywordsTime1)
            thread2 = Pthread(2, 'Thread-2', keywordsTime2)
            thread3 = Pthread(3, 'Thread-3', keywordsTime3)
            thread4 = Pthread(4, 'Thread-4', keywordsTime4)
            thread5 = Pthread(5, 'Thread-5', keywordsTime5)
            thread6 = Pthread(6, 'Thread-6', keywordsTime6)
            thread7 = Pthread(7, 'Thread-7', keywordsTime7)
            thread8 = Pthread(8, 'Thread-8', keywordsTime8)
            thread9 = Pthread(9, 'Thread-9', keywordsTime9)
            
            thread1.start()
            thread2.start()
            thread3.start()
            thread4.start()
            thread5.start()
            thread6.start()
            thread7.start()
            thread8.start()
            thread9.start()
            
            threads.append(thread1)
            threads.append(thread2)
            threads.append(thread3)
            threads.append(thread4)
            threads.append(thread5)
            threads.append(thread6)
            threads.append(thread7)
            threads.append(thread8)
            threads.append(thread9)
               
            frameCapture(keywordsTime10)   

            #wait all threads complete 
            for thread in threads:
                thread.join()
            
            print frames
            
            print 'success.'
            #Ouput preprocessed data as file
            with open (OUTPUT_PATH + 'preprocessedData.txt', 'w') as outputResult:
                for framePosition in frames:
                    outputResult.write('{' + str(framePosition) + '\n')
                    for face in frames[framePosition]:
                        outputResult.write( 'k' + str(face.keyword) + '\n')
                        outputResult.write( '(' +str(face.keywordID) + '\n')
                        outputResult.write( str(face.getPosition()) + '\n')
