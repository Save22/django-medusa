from django.core.management.base import BaseCommand
from django_medusa.renderers import StaticSiteRenderer
from django_medusa.utils import get_static_renderers

from optparse import make_option


class Command(BaseCommand):
    can_import_settings = True
    option_list = BaseCommand.option_list + (
        make_option('--host',
            action='store',
            dest='medusa_host',
            default=None,
            help='Specify custom target host for Medusa'),
        make_option('--bucket',
            action='store',
            dest='s3_bucket',
            default=None,
            help='Specify AWS storage bucket for S3 renderer'),
    )

    help = 'Looks for \'renderers.py\' in each INSTALLED_APP, which defines '\
           'a class for processing one or more URL paths into static files.'

    def handle(self, *args, **options):
        StaticSiteRenderer.initialize_output()

        for Renderer in get_static_renderers():
            r = Renderer()
            r.generate(options)

        StaticSiteRenderer.finalize_output()
