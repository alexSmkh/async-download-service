import os
from pathlib import Path
import logging

from aiohttp import web
import aiofiles
import asyncio


logger = logging.getLogger(__file__)


async def archive(request):
    response = web.StreamResponse()
    response.headers['Content-Type'] = 'application/octet-stream'
    response.headers['Content-Disposition'] = 'attachment; filename="photos.zip"'
    archive_hash = request.match_info.get('archive_hash')
    root_path = Path(__file__).parent.resolve()
    photos_root_path = os.path.join(root_path, 'test_photos')

    if archive_hash is None or not os.path.exists(os.path.join(photos_root_path, archive_hash)):
        return web.HTTPNotFound(body='The archive does not exist or has been deleted')

    await response.prepare(request)

    proc = await asyncio.create_subprocess_exec(
        'zip', '-r', '-', '.',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=os.path.join(Path(__file__).parent.resolve(), 'test_photos', archive_hash)
    )

    chunk_size_in_bytes = 100000
    try:
        while True:
            if proc.stdout.at_eof():
                break
            chunk_content = await proc.stdout.read(chunk_size_in_bytes)
            logging.info('Sending archive chunk ...')
            await response.write(chunk_content)

    except (asyncio.CancelledError, web.HTTPRequestTimeout):
        logging.info(f'The download was interrupted')
        raise
    finally:
        proc.kill()
        await proc.communicate()

    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archive),
    ])
    web.run_app(app)
