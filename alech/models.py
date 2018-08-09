from django.db import models


class ExportRequest(models.Model):
    name = models.CharField("Nom", max_length=50)


class ExportFile(models.Model):
    numero = models.IntegerField("Num")
    export = models.ForeignKey(ExportRequest, on_delete=models.CASCADE, related_name="files")
    file = models.FileField("Export file", upload_to="exports/", null=True)
