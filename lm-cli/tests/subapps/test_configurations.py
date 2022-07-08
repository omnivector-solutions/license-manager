import shlex

import httpx

from lm_cli.subapps.configurations import create, delete, get_one, list_all, style_mapper
from lm_cli.text_tools import unwrap


def test_list_all__makes_request_and_renders_results(
    respx_mock,
    make_test_app,
    dummy_configuration_data,
    dummy_domain,
    cli_runner,
    mocker,
):
    respx_mock.get(f"{dummy_domain}/config/all").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            json=dummy_configuration_data,
        ),
    )
    test_app = make_test_app("list-all", list_all)
    mocked_render = mocker.patch("lm_cli.subapps.configurations.render_list_results")
    result = cli_runner.invoke(test_app, ["list-all"])
    assert result.exit_code == 0, f"list-all failed: {result.stdout}"
    mocked_render.assert_called_once_with(
        dummy_configuration_data,
        title="Configurations List",
        style_mapper=style_mapper,
    )


def test_get_one__success(
    respx_mock,
    make_test_app,
    dummy_configuration_data,
    dummy_domain,
    cli_runner,
    mocker,
):
    respx_mock.get(f"{dummy_domain}/config/1").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            json=dummy_configuration_data[0],
        ),
    )
    test_app = make_test_app("get-one", get_one)
    mocked_render = mocker.patch("lm_cli.subapps.configurations.render_single_result")
    result = cli_runner.invoke(test_app, shlex.split("get-one --id=1"))

    assert result.exit_code == 0, f"get-one failed: {result.stdout}"

    mocked_render.assert_called_once_with(
        dummy_configuration_data[0],
        title="Configuration id 1",
    )


def test_create__success(
    respx_mock,
    make_test_app,
    dummy_domain,
    cli_runner,
    mocker,
):
    create_route = respx_mock.post(f"{dummy_domain}/config/").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            json={"message": "inserted 1"},
        ),
    )

    test_app = make_test_app("create", create)
    mocked_terminal_message = mocker.patch("lm_cli.subapps.configurations.terminal_message")
    result = cli_runner.invoke(
        test_app,
        shlex.split(
            unwrap(
                """
                create --id 1 --name 'Configuration 1' --product product1
                       --features '{"license1": 100}' --license-servers 'flexlm:127.0.0.1:1234'
                       --license-server-type 'flexlm' --grace-time 60
                """
            )
        ),
    )

    assert result.exit_code == 0, f"create failed: {result.stdout}"
    assert create_route.called

    mocked_terminal_message.assert_called_once_with(
        "The configuration was created successfully.",
        subject="Configuration creation succeeded",
    )


def test_delete__success(respx_mock, make_test_app, dummy_domain, cli_runner, mocker):
    delete_route = respx_mock.delete(f"{dummy_domain}/config/1").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            json={"message": "Deleted 1 from the configuration table."},
        )
    )

    test_app = make_test_app("delete", delete)
    mocked_terminal_message = mocker.patch("lm_cli.subapps.configurations.terminal_message")
    result = cli_runner.invoke(test_app, shlex.split("delete --id=1"))

    assert result.exit_code == 0, f"delete failed: {result.stdout}"
    assert delete_route.called

    mocked_terminal_message.assert_called_once_with(
        "The configuration was deleted successfully.",
        subject="Configuration delete succeeded",
    )
