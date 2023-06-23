import base64
import json
import requests

URL_API = "https://api.aermeal.io/site"

# edit these for your own query
# ------------
GUEST_ID = "1001"
TIME_FROM   = "20230401T0000"
TIME_TO     = "20230601T2359"
SITE_CODE = "[your site code]]"
EMAIL = "[user email address]"
PASSWORD = "[user password]"

DOWNLOAD_LOCATION = "./download"
# ------------

LOGIN_CREDENTIALS = { "site_code": SITE_CODE, "email": EMAIL, "password": PASSWORD }
LIST_PARAMS = { "site_code": SITE_CODE, "from_time" : TIME_FROM, "to_time" : TIME_TO, "guest_id": GUEST_ID }

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

    ###################################
    # Interpretring the depth image
    # format of the depth image:
    #     depth_scale // float (4 bytes)
    #     min_valid_depth // ushort (2 bytes)
    #     max_valid_depth // ushort (2 bytes)
    #     calculate_max_value // bool (1 byte)
    #     width // int (4 bytes)
    #     height // int (4 bytes)
    #     row_stride // int (4 bytes)
    #     data // byte[]
    ##################################
    # C sample code
    # uint16_t* temp = (uint16_t*)data;
    # for (int y = 0; y < height; y++)
    # {
    #    int pixel_index = y * width;
    #    for (int x = 0; x < width; x++)
    #    {
    #        float dt = scale * temp[pixel_index + x];
    #        std::cerr << x << "," << y << " - " << dt << "\n";
    #    }
    # }

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
        successes += download_meal_image(image["depth_filename"], headers)

        print(f"[{index+1}/{count}] {successes} / 3 files downloaded.     ")

    print("Download complete.")

if(__name__ == "__main__"):
    main()
