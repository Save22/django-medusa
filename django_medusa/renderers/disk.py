from __future__ import print_function
from django.conf import settings
from django.test.client import Client
import mimetypes
import os
from .base import COMMON_MIME_MAPS, BaseStaticSiteRenderer

__all__ = ('DiskStaticSiteRenderer', )


# Unfortunately split out from the class at the moment to allow rendering with
# several processes via `multiprocessing`.
# TODO: re-implement within the class if possible?
def _disk_render_path(args):
    client, path, view, host = args
    if not client:
        client = Client()
    if path:
        DEPLOY_DIR = settings.MEDUSA_DEPLOY_DIR
        realpath = path
        if path.startswith("/"):
            realpath = realpath[1:]

        if path.endswith("/"):
            needs_ext = True
        else:
            needs_ext = False

        output_dir = os.path.abspath(os.path.join(
            DEPLOY_DIR,
            os.path.dirname(realpath)
        ))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        outpath = os.path.join(DEPLOY_DIR, realpath)

    try:
        if host:
            resp = client.get(path, HTTP_HOST=host, follow=True)
        elif hasattr(settings, 'MEDUSA_HTTP_HOST'):
            resp = client.get(path, HTTP_HOST=settings.MEDUSA_HTTP_HOST, follow=True)
        else:
            resp = client.get(path)
        if resp.status_code != 200:
            raise Exception(resp.content)
        if needs_ext:
            mime = resp['Content-Type']
            mime = mime.split(';', 1)[0]

            # Check our override list above first.
            ext = COMMON_MIME_MAPS.get(
                mime,
                mimetypes.guess_extension(mime)
            )
            if ext:
                outpath += "index" + ext
            else:
                # Default to ".html"
                outpath += "index.html"
        print(outpath)
        with open(outpath, 'wb') as f:
            f.write(resp.content)
    except Exception, e:
        if hasattr(settings, 'MEDUSA_LOG'):
            with open(settings.MEDUSA_LOG, 'a') as logfile:
                logfile.write('#################\n')
                print(e)
                logfile.write(str(e))
                logfile.write('\n')
        return []


class DiskStaticSiteRenderer(BaseStaticSiteRenderer):

    def render_path(self, path=None, view=None, host=None):
        _disk_render_path((self.client, path, view, host))

    def generate(self, options):
        if getattr(settings, "MEDUSA_MULTITHREAD", False):
            # Upload up to ten items at once via `multiprocessing`.
            from multiprocessing import Pool, cpu_count

            print("Generating with up to %d processes..." % cpu_count())
            pool = Pool(cpu_count())

            pool.map_async(
                _disk_render_path,
                ((None, path, None) for path in self.paths),
                chunksize=5
            )
            pool.close()
            pool.join()
        else:
            # Use standard, serial upload.
            self.client = Client()
            if options['medusa_host']:
                host = options['medusa_host']
            elif hasattr(settings, 'MEDUSA_HTTP_HOST'):
                host = settings.MEDUSA_HTTP_HOST
            else:
                host = None
            self.host = host
            for path in self.paths:
                self.render_path(path=path, host=options['medusa_host'])

