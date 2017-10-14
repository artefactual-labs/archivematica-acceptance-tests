import os
import zipfile


def unzip(zip_path):
    directory_to_extract_to = os.path.dirname(zip_path)
    zip_ref = zipfile.ZipFile(zip_path, 'r')
    try:
        zip_ref.extractall(directory_to_extract_to)
    except:
        pass
    finally:
        zip_ref.close()
    if os.path.isdir(directory_to_extract_to):
        return directory_to_extract_to
    return None
