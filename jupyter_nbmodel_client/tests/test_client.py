#

from jupyter_nbmodel_client import NbModelClient


async def test_one(jp_serverapp, rtc_create_notebook):
    path, content = await rtc_create_notebook("test.ipynb")

    async with NbModelClient(jp_serverapp.connection_url, path, jp_serverapp.identity_provider.token):
        assert False
