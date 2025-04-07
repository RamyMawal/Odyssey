import cv2
import cv2.aruco as aruco
import numpy as np
import glob

def calibrate_camera_charuco():
    # Define Charuco board parameters (should match your board generation parameters)
    squares_x = 5         # Number of squares in X direction
    squares_y = 7         # Number of squares in Y direction
    square_length = 0.03  # In your chosen unit (e.g., meters)
    marker_length = 0.015 # Must be smaller than square_length

    # Use the same dictionary as for board generation
    dictionary = aruco.getPredefinedDictionary(aruco.DICT_5X5_100)

    # Create the Charuco board object (note: OpenCV uses (squares_x, squares_y))
    board = aruco.CharucoBoard((squares_x, squares_y), square_length, marker_length, dictionary)

    # Prepare lists to store detected charuco corners and ids from all images
    all_corners = []
    all_ids = []
    image_size = None

    # Load all calibration images from the specified directory
    images = glob.glob("calibration_images/*.jpg")  # change extension if needed
    print(f"Found {len(images)} images for calibration.")

    for fname in images:
        img = cv2.imread(fname)
        if img is None:
            continue  # Skip if image cannot be loaded

        # Save image size from first image
        if image_size is None:
            image_size = (img.shape[1], img.shape[0])  # (width, height)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Detect ArUco markers in the image
        corners, ids, rejected = aruco.detectMarkers(gray, dictionary)

        # If markers detected, interpolate to get Charuco corners
        if ids is not None and len(ids) > 0:
            retval, charuco_corners, charuco_ids = aruco.interpolateCornersCharuco(
                markerCorners=corners, markerIds=ids, image=gray, board=board)
            
            # If a sufficient number of charuco corners detected, store them
            if charuco_corners is not None and charuco_ids is not None and len(charuco_ids) > 20:
                all_corners.append(charuco_corners)
                all_ids.append(charuco_ids)
                
                # Optional: Draw the Charuco corners and display for verification
                img_drawn = aruco.drawDetectedMarkers(img.copy(), corners, ids)
                img_drawn = aruco.drawDetectedCornersCharuco(img_drawn, charuco_corners, charuco_ids)
                cv2.imshow('Charuco Corners', img_drawn)
                cv2.waitKey(100)
        else:
            print(f"No markers detected in image: {fname}")

    cv2.destroyAllWindows()

    if len(all_corners) == 0:
        print("No Charuco corners were detected in any image. Calibration failed.")
        return

    # Perform camera calibration using the detected Charuco corners
    ret, camera_matrix, dist_coeffs, rvecs, tvecs = aruco.calibrateCameraCharuco(
        charucoCorners=all_corners,
        charucoIds=all_ids,
        board=board,
        imageSize=image_size,
        cameraMatrix=None,
        distCoeffs=None)
    
    print("\nCalibration successful!")
    print("Camera matrix:")
    print(camera_matrix)
    print("\nDistortion coefficients:")
    print(dist_coeffs)
    print(f"\nRe-projection error: {ret}")

    # Optionally, undistort one of the images to visually validate calibration
    test_img = cv2.imread(images[0])
    undistorted_img = cv2.undistort(test_img, camera_matrix, dist_coeffs, None, camera_matrix)
    cv2.imwrite("undistorted_img.png", undistorted_img)
    cv2.imwrite("test_img.png", test_img)
    res_test_img = cv2.resize(test_img, dsize=(1280, 720), interpolation=cv2.INTER_CUBIC)
    res_undistorted_img  = cv2.resize(undistorted_img, dsize=(1280, 720), interpolation=cv2.INTER_CUBIC)
    cv2.imshow("Original Image", res_test_img)
    cv2.imshow("Undistorted Image", res_undistorted_img)
    cv2.waitKey(100)
    cv2.destroyAllWindows()

    # Save calibration results to a file (e.g., using NumPy's savez)
    np.savez("calibration_data.npz", camera_matrix=camera_matrix, dist_coeffs=dist_coeffs,
             rvecs=rvecs, tvecs=tvecs)




if __name__ == "__main__":
    calibrate_camera_charuco()
