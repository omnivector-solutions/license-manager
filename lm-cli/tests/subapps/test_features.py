import shlex

import httpx

from lm_cli.subapps.features import create, delete, get_one, list_all, style_mapper
from lm_cli.text_tools import unwrap


def test_list_all__makes_request_and_renders_results(
    respx_mock,
    make_test_app,
    dummy_feature_data,
    dummy_feature_data_for_printing,
    dummy_domain,
    cli_runner,
    mocker,
):
    """
    Test if the list all command fetches and renders the features result.
    """
    respx_mock.get(f"{dummy_domain}/lm/features/").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            json=dummy_feature_data,
        ),
    )
    test_app = make_test_app("list-all", list_all)
    mocked_render = mocker.patch("lm_cli.subapps.features.render_list_results")
    result = cli_runner.invoke(test_app, ["list-all"])
    assert result.exit_code == 0, f"list-all failed: {result.stdout}"
    mocked_render.assert_called_once_with(
        dummy_feature_data_for_printing,
        title="Features List",
        style_mapper=style_mapper,
    )


def test_get_one__success(
    respx_mock,
    make_test_app,
    dummy_booking_data,
    dummy_feature_data,
    dummy_feature_data_for_printing,
    dummy_domain,
    cli_runner,
    mocker,
):
    """
    Test if the get one command fetches and renders a single feature by id.
    """
    respx_mock.get(f"{dummy_domain}/lm/features/1").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            json=dummy_feature_data[0],
        ),
    )
    respx_mock.get(f"{dummy_domain}/lm/bookings/").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            json=dummy_booking_data,
        ),
    )
    test_app = make_test_app("get-one", get_one)
    mocked_render = mocker.patch("lm_cli.subapps.features.render_single_result")
    result = cli_runner.invoke(test_app, shlex.split("get-one --id=1"))

    assert result.exit_code == 0, f"get-one failed: {result.stdout}"

    mocked_render.assert_called_once_with(
        dummy_feature_data_for_printing[0],
        title="Feature id 1",
    )


def test_create__success(
    respx_mock,
    make_test_app,
    dummy_domain,
    cli_runner,
    mocker,
):
    """
    Test if the create command makes the request with the parsed arguments to create the feature.
    """
    create_route = respx_mock.post(f"{dummy_domain}/lm/features/").mock(
        return_value=httpx.Response(
            httpx.codes.CREATED, json={"id": 1, "name": "feature1", "product_id": 1, "config_id": 1, "reserved": 50}
        ),
    )

    test_app = make_test_app("create", create)
    mocked_terminal_message = mocker.patch("lm_cli.subapps.features.terminal_message")
    result = cli_runner.invoke(
        test_app,
        shlex.split(
            unwrap(
                """
                create --name 'feature1' --product-id 1 --config-id 1 --reserved 50
                """
            )
        ),
    )

    assert result.exit_code == 0, f"create failed: {result.stdout}"
    assert create_route.called

    mocked_terminal_message.assert_called_once_with(
        "The feature was created successfully.",
        subject="Feature creation succeeded.",
    )


def test_delete__success(respx_mock, make_test_app, dummy_domain, cli_runner, mocker):
    """
    Test if the delete command makes the request to delete the feature by id.
    """
    delete_route = respx_mock.delete(f"{dummy_domain}/lm/features/1").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            json={"message": "Feature deleted successfully."},
        )
    )

    test_app = make_test_app("delete", delete)
    mocked_terminal_message = mocker.patch("lm_cli.subapps.features.terminal_message")
    result = cli_runner.invoke(test_app, shlex.split("delete --id=1"))

    assert result.exit_code == 0, f"delete failed: {result.stdout}"
    assert delete_route.called

    mocked_terminal_message.assert_called_once_with(
        "The feature was deleted successfully.",
        subject="Feature delete succeeded",
    )
