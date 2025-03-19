import cv2
import cv2.aruco as aruco
import numpy as np

def main():
    # Define board parameters
    squares_x = 5         # Number of chessboard squares in the X direction
    squares_y = 7         # Number of chessboard squares in the Y direction
    square_length = 0.03    # Square side length in pixels (adjust as needed)
    marker_length = 0.015    # Marker side length in pixels (should be smaller than square_length)
    LENGTH_PX = 640   # total length of the page in pixels
    MARGIN_PX = 20    # size of the margin in pixels 
    # Choose a predefined dictionary. You can change the dictionary if desired.
    dictionary = aruco.getPredefinedDictionary(aruco.DICT_5X5_100)
    
    # Create the ChArUco board
    board = aruco.CharucoBoard((squares_x, squares_y), square_length, marker_length, dictionary)
    size_ratio = squares_y / squares_x
    board_img = aruco.CharucoBoard.generateImage(board, (LENGTH_PX, int(LENGTH_PX * size_ratio)), marginSize=MARGIN_PX)
    
    # Save the image to a PNG file
    cv2.imwrite("charuco_board.png", board_img)
    print("ChArUco board saved as 'charuco_board.png'")

if __name__ == "__main__":
    main()

