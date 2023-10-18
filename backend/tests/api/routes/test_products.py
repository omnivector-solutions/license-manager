from httpx import AsyncClient
from pytest import mark
from sqlalchemy import select

from lm_backend.api.models.product import Product
from lm_backend.permissions import Permissions


@mark.asyncio
async def test_add_product__success(
    backend_client: AsyncClient,
    inject_security_header,
    read_object,
):
    data = {
        "name": "Abaqus",
    }

    inject_security_header("owner1@test.com", Permissions.PRODUCT_EDIT)
    response = await backend_client.post("/lm/products", json=data)
    assert response.status_code == 201

    stmt = select(Product).where(Product.name == data["name"])
    fetched = await read_object(stmt)

    assert fetched.name == data["name"]


@mark.asyncio
async def test_get_all_products__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_products,
):
    inject_security_header("owner1@test.com", Permissions.PRODUCT_VIEW)
    response = await backend_client.get("/lm/products")

    assert response.status_code == 200

    response_products = response.json()
    assert response_products[0]["name"] == create_products[0].name


@mark.asyncio
async def test_get_all_products__with_search(
    backend_client: AsyncClient,
    inject_security_header,
    create_products,
):
    inject_security_header("owner1@test.com", Permissions.PRODUCT_VIEW)
    response = await backend_client.get(f"/lm/products?search{create_products[0].name}")

    assert response.status_code == 200

    response_product = response.json()
    assert response_product[0]["name"] == create_products[0].name


@mark.asyncio
async def test_get_all_products__with_sort(
    backend_client: AsyncClient,
    inject_security_header,
    create_products,
):
    inject_security_header("owner1@test.com", Permissions.PRODUCT_VIEW)
    response = await backend_client.get("/lm/products?sort_field=name&sort_ascending=false")

    assert response.status_code == 200

    response_products = response.json()
    assert response_products[0]["name"] == create_products[1].name
    assert response_products[1]["name"] == create_products[0].name


@mark.asyncio
async def test_get_product__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_product,
):
    id = create_one_product[0].id

    inject_security_header("owner1@test.com", Permissions.PRODUCT_VIEW)
    response = await backend_client.get(f"/lm/products/{id}")

    assert response.status_code == 200

    response_product = response.json()
    assert response_product["name"] == create_one_product[0].name


@mark.parametrize(
    "id",
    [
        0,
        -1,
        999999999,
    ],
)
@mark.asyncio
async def test_get_product__fail_with_bad_parameter(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_product,
    id,
):
    inject_security_header("owner1@test.com", Permissions.PRODUCT_VIEW)
    response = await backend_client.get(f"/lm/products/{id}")

    assert response.status_code == 404


@mark.asyncio
async def test_update_product__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_product,
    read_object,
):
    new_product = {
        "name": "Other Abaqus",
    }

    id = create_one_product[0].id

    inject_security_header("owner1@test.com", Permissions.PRODUCT_EDIT)
    response = await backend_client.put(f"/lm/products/{id}", json=new_product)

    assert response.status_code == 200

    stmt = select(Product).where(Product.id == id)
    fetch_product = await read_object(stmt)

    assert fetch_product.name == new_product["name"]


@mark.parametrize(
    "id",
    [
        0,
        -1,
        999999999,
    ],
)
@mark.asyncio
async def test_update_product__fail_with_bad_parameter(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_product,
    id,
):
    new_product = {"name": "Other Abaqus"}

    inject_security_header("owner1@test.com", Permissions.PRODUCT_EDIT)
    response = await backend_client.put(f"/lm/products/{id}", json=new_product)

    assert response.status_code == 404


@mark.asyncio
async def test_update_product__fail_with_bad_data(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_product,
):
    new_product = {"bla": "bla"}

    id = create_one_product[0].id

    inject_security_header("owner1@test.com", Permissions.PRODUCT_EDIT)
    response = await backend_client.put(f"/lm/products/{id}", json=new_product)

    assert response.status_code == 400


@mark.asyncio
async def test_delete_product__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_product,
    read_object,
):
    id = create_one_product[0].id

    inject_security_header("owner1@test.com", Permissions.PRODUCT_EDIT)
    response = await backend_client.delete(f"/lm/products/{id}")

    assert response.status_code == 200
    stmt = select(Product).where(Product.id == id)
    fetch_product = await read_object(stmt)

    assert fetch_product is None
