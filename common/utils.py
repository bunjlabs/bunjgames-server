import os
import shutil
import string
import zipfile
from urllib.parse import unquote

from rest_framework.exceptions import APIException
from django.conf import settings
from hashids import Hashids


class BadFormatException(APIException):
    status_code = 400


class BadStateException(APIException):
    status_code = 400


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


hashids = Hashids(salt=settings.SECRET_KEY, min_length=6, alphabet=string.ascii_uppercase + string.digits)


def generate_token(id):
    return hashids.encode(id)
