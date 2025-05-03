import cv2
import numpy as np
import os

calibration_data_path = "/home/ramy-mawal/Desktop/Projects/rc-robot-ui/calibration_data_latest.npz"

def pos_error_measure():
    cap = cv2.VideoCapture(2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1080)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    npz_file = np.load(calibration_data_path) 
    camera_matrix = npz_file['camera_matrix']
    dist_coeff = npz_file['dist_coeffs']
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_100)
    arucoParams = cv2.aruco.DetectorParameters()
    marker_length = 0.015

    rvec_list = []
    tvec_list = []

    for i in range(0, 1000):
        ret, frame = cap.read()
        if not ret:
            break

        undistorted_frame = cv2.undistort(frame, cameraMatrix=camera_matrix, distCoeffs=dist_coeff)
        gray = cv2.cvtColor(undistorted_frame, cv2.COLOR_BGR2GRAY)
        
        corners, ids, _ = cv2.aruco.detectMarkers(gray, dictionary, parameters=arucoParams)

        # cv2.imshow("Frame", undistorted_frame)
        # cv2.waitKey(100)
        if ids is not None:
            rvec, tvec, _ = cv2.aruco.estimatePoseSingleMarkers(corners, marker_length, camera_matrix, dist_coeff)
            # print(f"rvec: {rvec}")
            # print(f"tvec: {tvec}")

            for i in range(len(ids)):
                rvec_list.append(rvec[i])
                tvec_list.append(tvec[i])        
        
    cap.release()

    print(f"rvec_list: {rvec_list}")
    print(f"tvec_list: {tvec_list}")

    if len(rvec_list) == 0 or len(tvec_list) == 0:
        print("No markers detected.")
        return

    rvec_list = np.array(rvec_list)
    tvec_list = np.array(tvec_list)

    rvec_avg = np.average(rvec_list, axis=0)
    tvec_avg = np.average(tvec_list, axis=0)


    rvec_var = np.var(rvec_list, axis=0)
    tvec_var = np.var(tvec_list, axis=0)

    print(f"rvec_avg: {rvec_avg}")
    print(f"tvec_avg: {tvec_avg}")
    print(f"rvec_var: {rvec_var}")
    print(f"tvec_var: {tvec_var}")









if __name__ == "__main__":
    pos_error_measure()