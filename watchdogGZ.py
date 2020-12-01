import os
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import logging
import subprocess
from PIL import Image
import json

# --- Parameters for the compression ---
path_to_caesiumclt_exe = "./caesiumclt/caesiumclt.exe"
folder_to_watch = "."
compress_existing_images = False  # Can be True or False
compression_factor = 80  # 0 = lossless, 80 most common
wait_time_between_checks = 5  # seconds

# --- Don't modify anything beyond this point ---


logging.getLogger().setLevel(logging.INFO)
log_format = "(%(asctime)s)[%(levelname)s] %(message)s"
logging.basicConfig(format=log_format)
logging.captureWarnings(True)
fileList = []

def updateLog():
    print(fileList)
    a_file = open(".log/watchdog.json", "w")
    json.dump(fileList, a_file)
    a_file.close()

def compress_images():
    new_list = fileList.copy()
    for f in new_list:
        if new_list[f] == "waiting":
            try:
                cmd_line = '{} -q {} -e -o "{}" "{}"'.format(path_to_caesiumclt_exe, compression_factor, folder_to_watch, f)
                logging.info("Compressing {}...".format(f))
                res = subprocess.run(cmd_line, capture_output=True)
                logging.info(res.stdout.decode())
                if res.returncode != 0:
                    logging.error("Compression of {} failed with code {}".format(f, res.returncode))
                    fileList[f] = "error"
                else:
                    logging.info("Compression successful!")
                    fileList[f] = "done"
            except Exception as e:
                fileList["caesiumcltException"] = str(e)
                updateLog()
        updateLog()


def on_created(event):
    full_path = os.path.join(folder_to_watch, event.src_path)
    if full_path.lower().endswith('jpg') or full_path.lower().endswith('jpeg') :
        try:
            img = Image.open(event.src_path)
            if img.format == 'JPEG':
                fileList[event.src_path] = "waiting"
                updateLog()
        except:
            fileList[event.src_path] = "error"
            updateLog()

def on_deleted(event):
    pass


def on_modified(event):
    if event.src_path in fileList:
        if fileList[event.src_path] == "error":
            fileList[event.src_path] = "waiting"
    updateLog()


def on_moved(event):
    pass


if __name__ == "__main__":
    file_exists = os.path.isfile(".watchdog.json")
    if file_exists:
        with open('.log/watchdog.json') as json_file:
            fileList = json.load(json_file)
    else:
        fileList = {}
    patterns = "*"
    ignore_patterns = ""
    ignore_directories = False
    case_sensitive = True

    my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)
    my_event_handler.on_created = on_created
    my_event_handler.on_deleted = on_deleted
    my_event_handler.on_modified = on_modified

    my_event_handler.on_moved = on_moved

    path = folder_to_watch
    go_recursively = False
    my_observer = Observer()
    my_observer.schedule(my_event_handler, path, recursive=go_recursively)

    my_observer.start()
    try:
        while True:
            time.sleep(wait_time_between_checks)
            compress_images()
    except KeyboardInterrupt as e:
        my_observer.stop()
        my_observer.join()
        fileList["KeyboardInterrupt"]=str(e)
        updateLog()
