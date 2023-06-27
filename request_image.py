import base64
import json
import requests
import struct

import zipfile

URL_API = "https://api.aermeal.io/site"

# edit these for your own query
# ------------
GUEST_ID    = "[guest id]"
TIME_FROM   = "20210601T1001"
TIME_TO     = "20230701T2000"
SITE_CODE   = "[your site code]"
EMAIL       = "[email]"
PASSWORD    = "[password]"

DOWNLOAD_LOCATION = "./download"
# ------------

LOGIN_CREDENTIALS = { "site_code": SITE_CODE, "email": EMAIL, "password": PASSWORD }
LIST_PARAMS = { "guest_id": GUEST_ID, "from_time" : TIME_FROM, "to_time" : TIME_TO }

def request_body(dict): return json.dumps(dict)

# read, decode b64string, then write to file
def download_meal_image(filename, headers):
    try:
        response = requests.get(f"{URL_API}/meal/file", headers=headers, params={"filename": filename})
        file_bytes = base64.b64decode(response.json()["file"])
        with(open(f"{DOWNLOAD_LOCATION}/{filename}", "wb") as file):
            file.write(file_bytes)
        return 1
    except Exception as e:
        print(e)
        return 0

def download_depth_file(filename, headers):
    file_bytes = []
    try:
        print(f"Downloading file {filename}...")
        response = requests.get(f"{URL_API}/meal/file", headers=headers, params={"filename": filename})
        print(response.json())
        zip_bytes = base64.b64decode(response.json()["file"])

        # save the zip file first
        with(open(f"{DOWNLOAD_LOCATION}/{filename}", "wb") as file):
            file.write(zip_bytes)

        filename_depth = filename[:-4]
        # open the zip file and read the information
        with(zipfile.ZipFile(f"{DOWNLOAD_LOCATION}/{filename}") as zip):
            with(zip.open(f"{filename_depth}_rawdepth.dep", "r") as file):
                file_bytes = bytearray(file.read())

    except Exception as e:
        print(f"Failed to download depth zip: {e}")
        return 0

    depth_scale = 1
    min_valid_depth = 0
    max_valid_depth = 65535
    calculate_max_value = True
    width = 1920
    height = 1080
    row_stride = 3840

    temp = file_bytes
    for y in range(height):
        pixel_index = y * width
        for x in range(width):
            index = pixel_index + x
            dt = depth_scale * struct.unpack("H", temp[index:index+2])
            print(f"{x}, {y} - {dt}")

    return 1

def main():
    # login (get token)
    print("logging in...")
    response_login = requests.post(f"{URL_API}/login", data = request_body(LOGIN_CREDENTIALS))
    if(response_login.status_code != 200):
        print("Invalid login credentials")
    auth_token = response_login.json()["token"]
    headers = {"x-aervision-auth": auth_token}

    print(f"logged in with token {headers['x-aervision-auth']}")
    print(f"requesting meal list for date range {TIME_FROM} to {TIME_TO}...")

    # grab the list of images
    image_list = requests.get(f"{URL_API}/meals", headers = headers, params = LIST_PARAMS)
    print(image_list.text)
    images = image_list.json()

    # download each one by one
    count = len(images)
    print(f"{count} meals found.")
    for index, image in enumerate(images):
        successes = 0
        print(f"[{index+1}/{count}] downloading main image...", end='\r')
        successes += download_meal_image(image["image_filename"], headers)

        print(f"[{index+1}/{count}] downloading icon image...", end='\r')
        successes += download_meal_image(image["image_icon_filename"], headers)

        print(f"[{index+1}/{count}] downloading depth file...", end='\r')
        successes += download_depth_file(image["payload_zip_filename"], headers)

        print(f"[{index+1}/{count}] {successes} / 3 files downloaded.     ")

    print("Download complete.")

if(__name__ == "__main__"):
    main()
