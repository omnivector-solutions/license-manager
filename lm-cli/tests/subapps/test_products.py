import shlex

import httpx

from lm_cli.subapps.products import create, delete, get_one, list_all, style_mapper
from lm_cli.text_tools import unwrap


def test_list_all__makes_request_and_renders_results(
    respx_mock,
    make_test_app,
    dummy_product_data,
    dummy_domain,
    cli_runner,
    mocker,
):
    """
    Test if the list all command fetches and renders the license servers result.
    """
    respx_mock.get(f"{dummy_domain}/lm/products/").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            json=dummy_product_data,
        ),
    )

    test_app = make_test_app("list-all", list_all)
    mocked_render = mocker.patch("lm_cli.subapps.products.render_list_results")
    result = cli_runner.invoke(test_app, ["list-all"])
    assert result.exit_code == 0, f"list-all failed: {result.stdout}"
    mocked_render.assert_called_once_with(
        dummy_product_data,
        title="Products List",
        style_mapper=style_mapper,
    )


def test_get_one__success(
    respx_mock,
    make_test_app,
    dummy_product_data,
    dummy_domain,
    cli_runner,
    mocker,
):
    """
    Test if the get one command fetches and renders a single license server by id.
    """
    respx_mock.get(f"{dummy_domain}/lm/products/1").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            json=dummy_product_data[0],
        ),
    )
    test_app = make_test_app("get-one", get_one)
    mocked_render = mocker.patch("lm_cli.subapps.products.render_single_result")
    result = cli_runner.invoke(test_app, shlex.split("get-one --id=1"))

    assert result.exit_code == 0, f"get-one failed: {result.stdout}"

    mocked_render.assert_called_once_with(
        dummy_product_data[0],
        title="Product id 1",
    )


def test_create__success(
    respx_mock,
    make_test_app,
    dummy_domain,
    cli_runner,
    mocker,
):
    """
    Test if the create command makes the request with the parsed arguments to create the product.
    """
    create_route = respx_mock.post(f"{dummy_domain}/lm/products/").mock(
        return_value=httpx.Response(httpx.codes.CREATED, json={"id": 1, "name": "abaqus"}),
    )

    test_app = make_test_app("create", create)
    mocked_terminal_message = mocker.patch("lm_cli.subapps.products.terminal_message")
    result = cli_runner.invoke(
        test_app,
        shlex.split(
            unwrap(
                """
                create --name 'abaqus'
                """
            )
        ),
    )

    assert result.exit_code == 0, f"create failed: {result.stdout}"
    assert create_route.called

    mocked_terminal_message.assert_called_once_with(
        "The product was created successfully.",
        subject="Product creation succeeded.",
    )


def test_delete__success(respx_mock, make_test_app, dummy_domain, cli_runner, mocker):
    """
    Test if the delete command makes the request to delete the product by id.
    """
    delete_route = respx_mock.delete(f"{dummy_domain}/lm/products/1").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            json={"message": "Product deleted successfully."},
        )
    )

    test_app = make_test_app("delete", delete)
    mocked_terminal_message = mocker.patch("lm_cli.subapps.products.terminal_message")
    result = cli_runner.invoke(test_app, shlex.split("delete --id=1"))

    assert result.exit_code == 0, f"delete failed: {result.stdout}"
    assert delete_route.called

    mocked_terminal_message.assert_called_once_with(
        "The product was deleted successfully.",
        subject="Product delete succeeded",
    )
