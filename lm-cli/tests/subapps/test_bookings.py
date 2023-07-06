import httpx

from lm_cli.subapps.bookings import list_all, style_mapper


def test_list_all__makes_request_and_renders_results(
    respx_mock,
    make_test_app,
    dummy_booking_data,
    dummy_domain,
    cli_runner,
    mocker,
):
    """
    Test if the list all command fetches and renders the bookings result.
    """
    respx_mock.get(f"{dummy_domain}/lm/bookings/").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            json=dummy_booking_data,
        ),
    )
    test_app = make_test_app("list-all", list_all)
    mocked_render = mocker.patch("lm_cli.subapps.bookings.render_list_results")
    result = cli_runner.invoke(test_app, ["list-all"])
    assert result.exit_code == 0, f"list-all failed: {result.stdout}"
    mocked_render.assert_called_once_with(
        dummy_booking_data,
        title="Bookings List",
        style_mapper=style_mapper,
    )
