import os
import shutil
import zipfile
from urllib.parse import unquote


def unzip(filename, extract_dir):
    with zipfile.ZipFile(filename) as archive:
        for entry in archive.infolist():
            name = unquote(entry.filename)

            # don't extract absolute paths or ones with .. in them
            if name.startswith('/') or '..' in name:
                continue

            target = os.path.join(extract_dir, *name.split('/'))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            if not entry.is_dir():  # file
                with archive.open(entry) as source, open(target, 'wb') as dest:
                    shutil.copyfileobj(source, dest)
