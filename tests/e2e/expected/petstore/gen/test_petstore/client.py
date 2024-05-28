# This file is automatically @generated by Lapidary and should not be changed by hand.


__all__ = [
    'ApiClient',
]

import typing

from typing_extensions import Self
from typing import Annotated, Union
from lapidary.runtime import *


import test_petstore.components.schemas.ApiResponse.schema
import test_petstore.components.schemas.Order.schema
import test_petstore.components.schemas.Pet.schema
import test_petstore.components.schemas.User.schema
import test_petstore.paths.u_lstoreu_linventory.get.responses.u_o00.content.applicationu_ljson.schema.schema


class ApiClient(ClientBase):
    def __init__(
        self,
        *,
        base_url: str = 'https://petstore3.swagger.io/api/v3',
        **kwargs,
    ):
        super().__init__(
            base_url=base_url,
            **kwargs,
        )

    async def __aenter__(self) -> 'ApiClient':
        await super().__aenter__()
        return self

    async def __aexit__(self, __exc_type=None, __exc_value=None, __traceback=None) -> None:
        await super().__aexit__(__exc_type, __exc_value, __traceback)

    @put('/pet', security=[{'petstore_auth': ['write:pets', 'read:pets']}])
    async def updatePet(
        self: Self,
        request_body: Annotated[
            test_petstore.components.schemas.Pet.schema.Pet,
            RequestBody({
                'application/json': test_petstore.components.schemas.Pet.schema.Pet,
            }),
        ],
    ) -> Annotated[
        test_petstore.components.schemas.Pet.schema.Pet,
        Responses({
            '200': {
                'application/json': test_petstore.components.schemas.Pet.schema.Pet,
            },
            '400': {
            },
            '404': {
            },
            '405': {
            },
        })
    ]:
        pass

    @post('/pet', security=[{'petstore_auth': ['write:pets', 'read:pets']}])
    async def addPet(
        self: Self,
        request_body: Annotated[
            test_petstore.components.schemas.Pet.schema.Pet,
            RequestBody({
                'application/json': test_petstore.components.schemas.Pet.schema.Pet,
            }),
        ],
    ) -> Annotated[
        test_petstore.components.schemas.Pet.schema.Pet,
        Responses({
            '200': {
                'application/json': test_petstore.components.schemas.Pet.schema.Pet,
            },
            '405': {
            },
        })
    ]:
        pass

    @get('/pet/findByStatus', security=[{'petstore_auth': ['write:pets', 'read:pets']}])
    async def findPetsByStatus(
        self: Self,
        *,
        status_q: Annotated[typing.Union[None, str], Query('status', explode=True,)] = None,
    ) -> Annotated[
        list[test_petstore.components.schemas.Pet.schema.Pet],
        Responses({
            '200': {
                'application/json': list[test_petstore.components.schemas.Pet.schema.Pet],
            },
            '400': {
            },
        })
    ]:
        pass

    @get('/pet/findByTags', security=[{'petstore_auth': ['write:pets', 'read:pets']}])
    async def findPetsByTags(
        self: Self,
        *,
        tags_q: Annotated[typing.Union[None, list[str]], Query('tags', explode=True,)] = None,
    ) -> Annotated[
        list[test_petstore.components.schemas.Pet.schema.Pet],
        Responses({
            '200': {
                'application/json': list[test_petstore.components.schemas.Pet.schema.Pet],
            },
            '400': {
            },
        })
    ]:
        pass

    @get('/pet/{petId}', security=[{'api_key': []}, {'petstore_auth': ['write:pets', 'read:pets']}])
    async def getPetById(
        self: Self,
        *,
        petId_p: Annotated[int, Path('petId', )],
    ) -> Annotated[
        test_petstore.components.schemas.Pet.schema.Pet,
        Responses({
            '200': {
                'application/json': test_petstore.components.schemas.Pet.schema.Pet,
            },
            '400': {
            },
            '404': {
            },
        })
    ]:
        pass

    @post('/pet/{petId}', security=[{'petstore_auth': ['write:pets', 'read:pets']}])
    async def updatePetWithForm(
        self: Self,
        *,
        petId_p: Annotated[int, Path('petId', )],
        name_q: Annotated[typing.Union[None, str], Query('name', )] = None,
        status_q: Annotated[typing.Union[None, str], Query('status', )] = None,
    ) -> Annotated[
        None,
        Responses({
            '405': {
            },
        })
    ]:
        pass

    @delete('/pet/{petId}', security=[{'petstore_auth': ['write:pets', 'read:pets']}])
    async def deletePet(
        self: Self,
        *,
        petId_p: Annotated[int, Path('petId', )],
        api_key_h: Annotated[typing.Union[None, str], Header('api_key', )] = None,
    ) -> Annotated[
        None,
        Responses({
            '400': {
            },
        })
    ]:
        pass

    @post('/pet/{petId}/uploadImage', security=[{'petstore_auth': ['write:pets', 'read:pets']}])
    async def uploadFile(
        self: Self,
        *,
        petId_p: Annotated[int, Path('petId', )],
        additionalMetadata_q: Annotated[typing.Union[None, str], Query('additionalMetadata', )] = None,
    ) -> Annotated[
        test_petstore.components.schemas.ApiResponse.schema.ApiResponse,
        Responses({
            '200': {
                'application/json': test_petstore.components.schemas.ApiResponse.schema.ApiResponse,
            },
        })
    ]:
        pass

    @get('/store/inventory', security=[{'api_key': []}])
    async def getInventory(
        self: Self,
    ) -> Annotated[
        test_petstore.paths.u_lstoreu_linventory.get.responses.u_o00.content.applicationu_ljson.schema.schema.schema,
        Responses({
            '200': {
                'application/json': test_petstore.paths.u_lstoreu_linventory.get.responses.u_o00.content.applicationu_ljson.schema.schema.schema,
            },
        })
    ]:
        pass

    @post('/store/order')
    async def placeOrder(
        self: Self,
        request_body: Annotated[
            test_petstore.components.schemas.Order.schema.Order,
            RequestBody({
                'application/json': test_petstore.components.schemas.Order.schema.Order,
            }),
        ],
    ) -> Annotated[
        test_petstore.components.schemas.Order.schema.Order,
        Responses({
            '200': {
                'application/json': test_petstore.components.schemas.Order.schema.Order,
            },
            '405': {
            },
        })
    ]:
        pass

    @get('/store/order/{orderId}')
    async def getOrderById(
        self: Self,
        *,
        orderId_p: Annotated[int, Path('orderId', )],
    ) -> Annotated[
        test_petstore.components.schemas.Order.schema.Order,
        Responses({
            '200': {
                'application/json': test_petstore.components.schemas.Order.schema.Order,
            },
            '400': {
            },
            '404': {
            },
        })
    ]:
        pass

    @delete('/store/order/{orderId}')
    async def deleteOrder(
        self: Self,
        *,
        orderId_p: Annotated[int, Path('orderId', )],
    ) -> Annotated[
        None,
        Responses({
            '400': {
            },
            '404': {
            },
        })
    ]:
        pass

    @post('/user')
    async def createUser(
        self: Self,
        request_body: Annotated[
            test_petstore.components.schemas.User.schema.User,
            RequestBody({
                'application/json': test_petstore.components.schemas.User.schema.User,
            }),
        ],
    ) -> Annotated[
        test_petstore.components.schemas.User.schema.User,
        Responses({
            'default': {
                'application/json': test_petstore.components.schemas.User.schema.User,
            },
        })
    ]:
        pass

    @post('/user/createWithList')
    async def createUsersWithListInput(
        self: Self,
        request_body: Annotated[
            list[test_petstore.components.schemas.User.schema.User],
            RequestBody({
                'application/json': list[test_petstore.components.schemas.User.schema.User],
            }),
        ],
    ) -> Annotated[
        test_petstore.components.schemas.User.schema.User,
        Responses({
            '200': {
                'application/json': test_petstore.components.schemas.User.schema.User,
            },
            'default': {
            },
        })
    ]:
        pass

    @get('/user/login')
    async def loginUser(
        self: Self,
        *,
        username_q: Annotated[typing.Union[None, str], Query('username', )] = None,
        password_q: Annotated[typing.Union[None, str], Query('password', )] = None,
    ) -> Annotated[
        str,
        Responses({
            '200': {
                'application/json': str,
            },
            '400': {
            },
        })
    ]:
        pass

    @get('/user/logout')
    async def logoutUser(
        self: Self,
    ) -> Annotated[
        None,
        Responses({
            'default': {
            },
        })
    ]:
        pass

    @get('/user/{username}')
    async def getUserByName(
        self: Self,
        *,
        username_p: Annotated[str, Path('username', )],
    ) -> Annotated[
        test_petstore.components.schemas.User.schema.User,
        Responses({
            '200': {
                'application/json': test_petstore.components.schemas.User.schema.User,
            },
            '400': {
            },
            '404': {
            },
        })
    ]:
        pass

    @put('/user/{username}')
    async def updateUser(
        self: Self,
        request_body: Annotated[
            test_petstore.components.schemas.User.schema.User,
            RequestBody({
                'application/json': test_petstore.components.schemas.User.schema.User,
            }),
        ],
        *,
        username_p: Annotated[str, Path('username', )],
    ) -> Annotated[
        None,
        Responses({
            'default': {
            },
        })
    ]:
        pass

    @delete('/user/{username}')
    async def deleteUser(
        self: Self,
        *,
        username_p: Annotated[str, Path('username', )],
    ) -> Annotated[
        None,
        Responses({
            '400': {
            },
            '404': {
            },
        })
    ]:
        pass