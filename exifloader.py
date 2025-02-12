import piexif
from exif import Image
import sys
import os

def print_all_items(items):
    print(f"There are {len(items)} items to be printed: ")
    for item in items:
        print(" " + item)


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

main()