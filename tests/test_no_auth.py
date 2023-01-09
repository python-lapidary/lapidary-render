import sys
import tempfile
from pathlib import Path
from unittest import IsolatedAsyncioTestCase

from lapidary.runtime import openapi
from lapidary.runtime.http_consts import MIME_JSON
from lapidary.runtime.model import get_client_model, get_resolver
from lapidary.runtime.module_path import ModulePath
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from lapidary.render.client import render_client
from lapidary.render.config import Config


class RenderExecTestCase(IsolatedAsyncioTestCase):
    async def test_render_no_auth(self):
        model = openapi.OpenApiModel(
            openapi='3.0.3',
            info=openapi.Info(title='', version=''),
            paths=openapi.Paths(**{
                '/path': openapi.PathItem(get=openapi.Operation(
                    operationId='hello_world',
                    responses=openapi.Responses(
                        default=openapi.Response(
                            description='',
                            content={MIME_JSON: openapi.MediaType(
                                schema=openapi.Schema(
                                    type=openapi.Type.object,
                                    required=['myprop'],
                                    properties=dict(
                                        myprop=openapi.Schema(type=openapi.Type.string)
                                    )
                                )
                            )}
                        )
                    )
                ))
            })
        )

        async def handler(_):
            return JSONResponse(dict(myprop='hello world'))

        app = Starlette(debug=True, routes=[
            Route('/path', handler),
        ])

        with tempfile.TemporaryDirectory() as tmp:
            render_client(model, Path(tmp) / 'testproj', Config(package='testproj'))
            sys.path.append(tmp + '/testproj/gen')

            from testproj.client import ApiClient, Auth

            client = ApiClient(
                auth=Auth(),
                base_url='https://example.com/',
                _app=app,
                _model=get_client_model(model, ModulePath('testproj'), get_resolver(model, 'testproj')))
            self.assertEqual('hello world', (await client.hello_world()).myprop)
