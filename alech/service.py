import zipfile
import numpy as np
import logging

import uuid
import io
from django.core.files.base import ContentFile

from alech.models import ExportFile

X_1KB = 1024
X_1MB = 1024 * 1024
X_5MB = 5 * X_1MB


class RotatingExportFile:
    log = logging.getLogger(__name__)
    limit_zfile_size = X_5MB

    def __init__(self, export_request, limit_size=None):
        if limit_size:
            self.limit_zfile_size = limit_size
        self.export = export_request
        self.in_memory_buffer = io.BytesIO()
        self.cpt = self.retrieve_export_files_count() + 1

    def retrieve_export_files_count(self):
        return self.export.files.count()

    def add_file(self, path, bytestr):
        with zipfile.ZipFile(self.in_memory_buffer, "a", compression=zipfile.ZIP_DEFLATED) as zfile:
            zfile.writestr(path, bytestr)

        self.verify_size_and_commit_file_if_limit_exceeded_and_not_empty()

    def close(self):
        self.save()
        self.log.info("Finalize last save...")

    def save(self):
        if len(self.in_memory_buffer.getvalue()) == 0:
            self.log.info("Empty zip, pass...")
            return None

        try:
            export_file = ExportFile(
                numero=self.cpt,
                export=self.export
            )

            export_file.file.save(
                "Export n°{} - part {}.zip".format(self.export.pk, self.cpt),
                ContentFile(self.in_memory_buffer.getvalue())
            )

            self.cpt += 1
            self.in_memory_buffer = io.BytesIO()
            return export_file
        except Exception as exc:
            self.log.exception("Error when saving", exc)
            return None

    def verify_size_and_commit_file_if_limit_exceeded_and_not_empty(self):
        if len(self.in_memory_buffer.getvalue()) >= self.limit_zfile_size:
            export_file = self.save()
            if not export_file:
                self.log.info(
                    "ZIP File limit exceeded. Saved ExportFile pk {}, Initializing new ExportFile...".format(export_file.pk)
                )
                return True
        return False


def generate_random_byte_string(size):
    bytes_str = np.random.bytes(size)
    return str(uuid.uuid4()), bytes_str


def generate_zero_byte_string(size):
    bytes_str = b"\0" * size
    return str(uuid.uuid4()), bytes_str
