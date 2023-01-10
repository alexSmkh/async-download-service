import os
from pathlib import Path

from aiohttp import web
import aiofiles
import asyncio


async def archive(request):
    response = web.StreamResponse()
    response.headers['Content-Type'] = 'application/octet-stream'
    response.headers['Content-Disposition'] = 'attachment; filename="photos.zip"'
    archive_hash = request.match_info.get('archive_hash')

    await response.prepare(request)

    proc = await asyncio.create_subprocess_exec(
        'zip', '-r', '-', '.',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=os.path.join(Path(__file__).parent.resolve(), 'test_photos', archive_hash)
    )

    chunk_size_in_bytes = 100000
    while True:
        if not proc.stdout.at_eof():
            chunk_content = await proc.stdout.read(chunk_size_in_bytes)
            await response.write(chunk_content)
            continue
        break

    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archive),
    ])
    web.run_app(app)
