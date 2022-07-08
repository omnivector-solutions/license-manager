import httpx

from lm_cli.subapps.licenses import list_all, style_mapper


def test_list_all__makes_request_and_renders_results(
    respx_mock,
    make_test_app,
    dummy_license_data,
    dummy_domain,
    cli_runner,
    mocker,
):
    respx_mock.get(f"{dummy_domain}/license/all").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            json=dummy_license_data,
        ),
    )
    test_app = make_test_app("list-all", list_all)
    mocked_render = mocker.patch("lm_cli.subapps.licenses.render_list_results")
    result = cli_runner.invoke(test_app, ["list-all"])
    assert result.exit_code == 0, f"list-all failed: {result.stdout}"
    mocked_render.assert_called_once_with(
        dummy_license_data,
        title="Licenses List",
        style_mapper=style_mapper,
    )
