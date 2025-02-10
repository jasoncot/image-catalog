from exif import Image
import os
import hashlib
import shutil

def read_dir(base_path="."):
    files = []
    dirs = []
    if base_path == "./duplicates" or base_path == "./output":
        return files
    
    print(f"Reading directory '{base_path}' ... ", end="")
    dir_list = os.listdir(base_path)
    print(f"done ({len(dir_list)} files)")

    for file in dir_list:
        sub_path = os.path.join(base_path, file)
        if os.path.isfile(sub_path):
            files.append(sub_path)
        if os.path.isdir(sub_path):
            dirs.append(sub_path)

    for sub_dir in dirs:
        files += read_dir(sub_dir)

    return files

def read_file(file_path):
    file_obj = open(file_path, "rb")
    contents = file_obj.read()
    file_obj.close()
    return contents

def hash_contents(file_contents):
    hash = hashlib.new('sha1')
    hash.update(file_contents)
    return hash.hexdigest()

def append_to_file(file, text):
    with open(file, "a") as my_file:
        my_file.write(text)

def append_source_to_data_file(path, filename):
    append_to_file(os.path.join(path, "source_data.txt"), f"{filename}\n")

def append_error(error_text):
    append_to_file(os.path.join(".", "output", "errors.txt"), error_text)

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

# take a path to a file, see if it's a jpg/jpeg and if it is, read the exif data
# returns a string that should be the new file name based on the exif data
# would like to seperate out paths like year/{month_no}_{month_name}/{year}{month_no}{day_no}{hour}{minute}.{ext}
# otherwise, just return the file name of the path
def generate_new_filename(path):
    split_ext = os.path.splitext(path)
    ext = split_ext[1].lower()
    if ext != ".jpg" and ext != ".jpeg":
        return "", os.path.basename(path)
    
    datetime = ""
    with open(path, 'rb') as image_file:
        my_image = Image(image_file)
        datetime = ""
        try:
            datetime = my_image.datetime
            return build_path_from_exif_datetime(datetime)
        except:
            # need to find alternate route here
            append_error(f"\"{path}\" did not contain datetime exif data.\n")

    print(f"datetime: {datetime}")
    return "", datetime


DO_COPY = False
DO_MOVE = False

def main():
    # establish a duplicates directory
    starting_point = "."
    duplicates_dir = os.path.join(starting_point, "duplicates")
    os.makedirs(duplicates_dir, exist_ok=True)

    print(f"Reading files starting at {starting_point}")

    files_in_dir = read_dir(starting_point)
    print("There were %d files in the directory '%s'" % (len(files_in_dir), starting_point))

    cache = {}
    coll = [];

    file_index = 0
    file_to_hash_list = []
    skipped_files = []

    for path in files_in_dir:
        print("Reading file %d" % (file_index), end="\r")
        file_index += 1

        # make sure we aren't diving back into the duplicates or output paths
        if path.startswith("./duplicates") or path.startswith("./output"):
            continue
        
        # skip these extensions
        split_ext = os.path.splitext(path)
        cur_ext = split_ext[1].lower()
        if cur_ext != ".jpg" and cur_ext != ".jpeg":
            skipped_files.append(path)
            continue
        
        file_to_hash_list.append([path, hash_contents(read_file(path))])

    # now that we have read in all the files and created hashes
    # determine which files are duplicates
    for pair in file_to_hash_list:
        path, hash_value = pair
        if hash_value in cache:
            hash_dup_dir = os.path.join(duplicates_dir, hash_value)
            os.makedirs(hash_dup_dir, exist_ok=True)
            existing_files = read_dir(hash_dup_dir)
            my_path = cache[hash_value][0]

            if len(existing_files) > 0:
                split_ext = os.path.splitext(path)
                dst_filename = f"duplicate_file_{len(existing_files)}{split_ext[1]}"
                if DO_COPY:
                    shutil.copy(path, os.path.join(hash_dup_dir, dst_filename))
                elif DO_MOVE:
                    shutil.move(path, os.path.join(hash_dup_dir, dst_filename))
                else:
                    print(f"src: {path}, dst: {os.path.join(hash_dup_dir, dst_filename)}")
                append_source_to_data_file(hash_dup_dir, f"{dst_filename}: {path}")
            else:
                split_ext = os.path.splitext(my_path)
                dst_filename = f"duplicate_file_0{split_ext[1]}"
                if DO_COPY:
                    shutil.copy(my_path, os.path.join(hash_dup_dir, dst_filename))
                elif DO_MOVE:
                    shutil.move(my_path, os.path.join(hash_dup_dir, dst_filename))
                else:
                    print(f"src: {my_path}, dst: {os.path.join(hash_dup_dir, dst_filename)}")
                append_source_to_data_file(hash_dup_dir, f"{dst_filename}: {my_path}")

                split_ext = os.path.splitext(path)
                dst_filename = f"duplicate_file_1{split_ext[1]}"
                if DO_COPY:
                    shutil.copy(path, os.path.join(hash_dup_dir, dst_filename))
                elif DO_MOVE:
                    shutil.move(path, os.path.join(hash_dup_dir, dst_filename))
                else:
                    print(f"src: {path}, dst: {os.path.join(hash_dup_dir, dst_filename)}")
                append_source_to_data_file(hash_dup_dir, f"{dst_filename}: {path}")

            cache[hash_value] = (my_path, True)
            coll.append((path, cache[hash_value]))
        else:
            cache[hash_value] = (path, False)

    # make sure we have our output directory configured
    output_dir = os.path.join(starting_point, "output")
    os.makedirs(output_dir, exist_ok=True)

    output_map = {}

    # We want to move files here when they did not collide with another file
    for tup in cache.values():
        (file_path, has_duplicates) = tup
        if has_duplicates:
            # skip for now
            continue
        rel_path, new_filename = generate_new_filename(file_path)
        os.makedirs(os.path.join(output_dir, rel_path), exist_ok=True)

        target_output_file = os.path.join(output_dir, rel_path, new_filename)
        date_col_index = None
        if target_output_file in output_map:
            output_map[target_output_file] += 1
            date_col_index = output_map[target_output_file]
        else:
            output_map[target_output_file] = 1

        if date_col_index is not None:
            new_filename += f"_{date_col_index}"

        new_filename += ".jpg"

        if DO_COPY:
            shutil.copy(file_path, os.path.join(output_dir, rel_path, new_filename))
        elif DO_MOVE:
            shutil.move(file_path, os.path.join(output_dir, rel_path, new_filename))
        else:
            print(f"src: {file_path}, dst: {os.path.join(output_dir, rel_path, new_filename)}")
        
    if len(coll) > 0:
        print("There were %d collisions" % (len(coll)))

main()