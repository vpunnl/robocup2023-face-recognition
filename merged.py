from deepface import DeepFace
import cv2
import os
from custom_socket import CustomSocket
import socket
import json
import numpy as np
import traceback

DEEPFACE_MODEL = "Facenet512"
REPRESENTATION = "representations_facenet512.pkl"
DETECTOR_BACKEND = "ssd"

def main():
    HOST = socket.gethostname()
    PORT = 10011

    server = CustomSocket(HOST, PORT)
    server.startServer()

    while True:
        conn, addr = server.sock.accept()
        print("Client connected from", addr)

        while True:
            res = dict()
            try:
                dataraw = server.recvMsg(conn)
                # print("raw",type(dataraw))
                data = dataraw.split(b'bytesplitter')
                # print("data",type(data))
                height = int(data[2].decode())
                width = int(data[3].decode())
               
                frame = np.frombuffer(data[1], dtype=np.uint8).reshape(height, width, 3)
                results = DeepFace.extract_faces(frame, detector_backend= DETECTOR_BACKEND, enforce_detection= False, align= True, target_size= frame.shape[:-1])

                #recog
                if data[0].decode() == 'recog':
                    registered_name = data[4].decode()
                    cv2.imwrite("./people/{}.jpg".format(registered_name), frame)

                    feedback = bytes("Image and name received",'utf-8')
                    msg = server.sendMsg(conn, feedback)

                    try:
                        os.remove(f"./people/{REPRESENTATION}")
                    except:
                        print("No files found")

                #detect
                if data[0].decode() == 'detect':
                    for i, face in enumerate(results):
                        coordinates = face["facial_area"]
                        face_x, face_y, face_w, face_h = coordinates["x"], coordinates["y"], coordinates["w"], coordinates["h"]
                        imagePath = "./captures/capture{}.jpg".format(i)
                        face_crop = frame[face_y:face_y+face_h, face_x:face_x+face_w]

                        if len(os.listdir("./people")) != 0: 
                            result = DeepFace.find(img_path = face_crop, db_path = "./people", model_name=DEEPFACE_MODEL, enforce_detection = False, silent=True, align=True)

                            if len(result[0]) > 0:
                                recog_name = result[0]["identity"][0][9:-4]
                                cv2.putText(frame, recog_name,  (coordinates["x"], coordinates["y"]), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 1)
                                print("Recognized: " + recog_name)
                                res = {"name" : recog_name}
                                server.sendMsg(conn, json.dumps(res))
                            else:
                                res = {}
                                server.sendMsg(conn, json.dumps(res))   
                        else:
                            res = {}
                            server.sendMsg(conn, json.dumps(res))   

                        cv2.rectangle(frame, (face_x, face_y), (face_x+face_w, face_y+face_h),  (255,255,0), 3)


            except Exception as e:
                traceback.print_exc()
                print(e)
                print("Connection Closed")
                break
        
if __name__ == '__main__':
    main()