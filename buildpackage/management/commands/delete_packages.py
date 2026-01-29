from django.core.management.base import BaseCommand
from buildpackage.models import Package
import datetime

class Command(BaseCommand):

    def handle(self, *args, **options):
        
        one_hour_ago = datetime.datetime.now() - datetime.timedelta(minutes=60)
        packages = Package.objects.filter(finished_date__lt=one_hour_ago)
        packages.delete()

        one_day_ago = datetime.datetime.now() - datetime.timedelta(hours=24)
        packages = Package.objects.filter(created_date__lt=one_day_ago)
        packages.delete()


