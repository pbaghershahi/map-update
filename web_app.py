from flask import request, render_template, Flask
from time import sleep
import numpy as np
import threading

app = Flask(__name__)
global_running = True

@app.route('/',methods=['GET','POST'])
def my_maps():
    coordinates = None
    if request.method == 'POST':
        returned_data = request.get_json()
        if 'coordinates' in returned_data:
            coordinates = request.get_json()['coordinates'][0]
            set_bbox(coordinates)
            print(coordinates)
        elif 'submit' in returned_data:
            if coordinates:
                set_running(False)
            else:
                print('Please select an area.')

    return render_template('index.html')

def set_bbox(coordinates):
    coordinates = np.array(coordinates)
    print(coordinates)
    min_lat = np.min(coordinates[:, 1])
    max_lat = np.max(coordinates[:, 1])
    min_lon = np.min(coordinates[:, 0])
    max_lon = np.max(coordinates[:, 0])
    with open('./utils/bounding_box.txt', 'w') as bbox_file:
        txt2write = f'NORTH_LATITUDE={max_lat}\n' + \
                    f'SOUTH_LATITUDE={min_lat}\n' + \
                    f'EAST_LONGITUDE={max_lon}\n' + \
                    f'WEST_LONGITUDE={min_lon}'
        bbox_file.write(txt2write)

def set_running(set_value):
    global global_running
    global_running = set_value

def flaskThread():
    app.run(debug=True, use_reloader=False)

def sample():
    while global_running:
        print('here')
        sleep(1)
    print('finished')

if __name__ == '__main__':
    threading.Thread(target=flaskThread).start()
    sample()