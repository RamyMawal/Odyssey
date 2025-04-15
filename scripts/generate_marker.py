import cv2
import cv2.aruco as aruco

id = 2

def generate_aruco_marker(marker_id=0, marker_size=200, save_path="."):
    file_name = f"{save_path}/marker_5X5_{marker_id}.png"
    
    dictionary = aruco.getPredefinedDictionary(aruco.DICT_5X5_100)
    marker_image = aruco.generateImageMarker(dictionary, marker_id, marker_size)

    cv2.imwrite(f"{file_name}", marker_image)
    print(f"Marker ID {marker_id} saved as '{file_name}'")

if __name__ == "__main__":
    generate_aruco_marker(marker_id=id, save_path="./markers")  