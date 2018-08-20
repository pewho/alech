import io
import tempfile
from zipfile import ZipFile

from django.test import TestCase, override_settings
import uuid

from alech.models import ExportRequest
from alech.service import X_1MB, generate_random_byte_string, RotatingExportFile, X_5MB, generate_zero_byte_string


class TestGenerateRandomStr(TestCase):
    def test_generate_random(self):
        name, gnr_str = generate_random_byte_string(X_1MB)
        self.assertEqual(len(gnr_str), X_1MB)
        self.assertIsInstance(gnr_str, bytes)
        try:
            uuid.UUID(name)
        except TypeError:
            self.assertFalse(False, "name is not valid : {}".format(name))

    def test_generate_zero(self):
        name, gnr_str = generate_zero_byte_string(X_1MB)
        self.assertEqual(len(gnr_str), X_1MB)
        self.assertIsInstance(gnr_str, bytes)
        try:
            uuid.UUID(name)
        except TypeError:
            self.assertFalse(False, "name is not valid : {}".format(name))


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class TestRotatingExportFile(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.export = ExportRequest.objects.create(name="TEST")

    def test_init(self):
        zipfile = RotatingExportFile(self.export)
        self.assertEqual(zipfile.export, self.export)
        self.assertEqual(zipfile.in_memory_buffer.getvalue(), io.BytesIO().getvalue())
        self.assertEqual(zipfile.cpt, 1)
        self.assertEqual(zipfile.limit_zfile_size, X_5MB)

    def test_add_file(self):
        filename, bytes_str = generate_random_byte_string(X_1MB)

        zipfile = RotatingExportFile(self.export)
        zipfile.add_file(filename, bytes_str)

        compr_result = ZipFile(zipfile.in_memory_buffer, "r")

        list_file = compr_result.filelist
        self.assertEqual(len(list_file), 1)
        self.assertEqual(list_file[0].filename, filename)
        self.assertEqual(list_file[0].file_size, X_1MB)

    def test_save(self):
        filename, bytes_str = generate_random_byte_string(X_1MB)
        zipfile = RotatingExportFile(self.export)
        zipfile.add_file(filename, bytes_str)
        zipfile.save()

        self.export.refresh_from_db()
        self.assertEqual(self.export.files.count(), 1)
        export_file = self.export.files.last()
        self.assertEqual(export_file.numero, 1)
        self.assertEqual(export_file.export, self.export)
        self.assertIsNotNone(export_file.file)

    def test_overflow_limit_with_big_file(self):
        big_file_name, big_bytes_str = generate_random_byte_string(5 * X_5MB)
        filename, bytes_str = generate_random_byte_string(X_1MB)

        zipfile = RotatingExportFile(self.export)
        zipfile.add_file(big_file_name, big_bytes_str)

        self.export.refresh_from_db()
        self.assertEqual(self.export.files.count(), 1)

        zipfile.add_file(filename, bytes_str)
        zipfile.close()
        self.export.refresh_from_db()
        self.assertEqual(self.export.files.count(), 2)

    def test_close_with_empty_zip(self):
        zipfile = RotatingExportFile(self.export)
        zipfile.add_file(*generate_random_byte_string(X_5MB*5))
        self.export.refresh_from_db()
        self.assertEqual(self.export.files.count(), 1)

        zipfile.close()
        self.export.refresh_from_db()
        self.assertEqual(self.export.files.count(), 1)

    def test_overflow_limit_with_multi_small_files(self):
        zipfile = RotatingExportFile(self.export)

        for _ in range(0, 15):
            zipfile.add_file(*generate_random_byte_string(X_1MB))

        self.export.refresh_from_db()
        self.assertEqual(self.export.files.count(), 3)

    def test_zip_handle_compression(self):
        zipfile = RotatingExportFile(self.export)

        zipfile.add_file(*generate_zero_byte_string(X_5MB))
        zipfile.close()
        self.assertNotEqual(len(zipfile.in_memory_buffer.getvalue()), X_5MB)

    def test_big_file(self):
        zipfile = RotatingExportFile(self.export)

        zipfile.add_file(*generate_random_byte_string(1000*X_1MB))
        zipfile.close()
