# import piexif
from exif import Image
import sys
import os

def print_all_items(items):
    print(f"There are {len(items)} items to be printed: ")
    for item in items:
        print(" " + item)

MONTH_NAMES = ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"]

def build_path_from_exif_datetime(datetime):
    path = None
    filename = None
    (left, _, right) = datetime.partition(" ")
    if left.find(":") != -1:
        parts = left.split(":")
        year, month, day = parts[0], int(parts[1]), parts[2]
        month_str = "%02d_%s" % (month, MONTH_NAMES[month - 1])
        path = os.path.join(f"{year}", month_str)
        filename = f"{year}{parts[1]}{day}"

    if right is not None:
        parts = right.split(":")
        hour, minute, second = parts[0], parts[1], parts[2]
        if filename is None:
            filename = ""
        filename += f"_{hour}{minute}{second}"

    return path, filename

def main():
    n = len(sys.argv)
    if n < 1:
        return None

    target_image = sys.argv[1]
    print("trying to retrieve exif data for ", target_image)

    if os.path.isfile(target_image):
        with open(target_image, 'rb') as image_file:
            image_bytes = image_file.read()

            my_image = Image(image_bytes)
            if my_image.has_exif:
                print("keys are as follows:")
                print_all_items(my_image.list_all())
            else:
                print("there was no exif?")
                return

            print("datetime: " + my_image.datetime)
            path, filename = build_path_from_exif_datetime(my_image.datetime)
            print("path: " + path)
            print("filename: " + filename)


main()