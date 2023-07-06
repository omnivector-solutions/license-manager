import shlex

import httpx

from lm_cli.subapps.clusters import create, delete, get_one, list_all, style_mapper
from lm_cli.text_tools import unwrap


def test_list_all__makes_request_and_renders_results(
    respx_mock,
    make_test_app,
    dummy_cluster_data,
    dummy_cluster_data_for_printing,
    dummy_domain,
    cli_runner,
    mocker,
):
    """
    Test if the list all command fetches and renders the clusters result.
    """
    respx_mock.get(f"{dummy_domain}/lm/clusters/").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            json=dummy_cluster_data,
        ),
    )
    test_app = make_test_app("list-all", list_all)
    mocked_render = mocker.patch("lm_cli.subapps.clusters.render_list_results")
    result = cli_runner.invoke(test_app, ["list-all"])
    assert result.exit_code == 0, f"list-all failed: {result.stdout}"
    mocked_render.assert_called_once_with(
        dummy_cluster_data_for_printing,
        title="Clusters List",
        style_mapper=style_mapper,
    )


def test_get_one__success(
    respx_mock,
    make_test_app,
    dummy_cluster_data,
    dummy_cluster_data_for_printing,
    dummy_domain,
    cli_runner,
    mocker,
):
    """
    Test if the get one command fetches and renders a single cluster by id.
    """
    respx_mock.get(f"{dummy_domain}/lm/clusters/1").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            json=dummy_cluster_data[0],
        ),
    )
    test_app = make_test_app("get-one", get_one)
    mocked_render = mocker.patch("lm_cli.subapps.clusters.render_single_result")
    result = cli_runner.invoke(test_app, shlex.split("get-one --id=1"))

    assert result.exit_code == 0, f"get-one failed: {result.stdout}"

    mocked_render.assert_called_once_with(
        dummy_cluster_data_for_printing[0],
        title="Cluster id 1",
    )


def test_create__success(
    respx_mock,
    make_test_app,
    dummy_domain,
    cli_runner,
    mocker,
):
    """
    Test if the create command makes the request with the parsed arguments to create the cluster.
    """
    create_route = respx_mock.post(f"{dummy_domain}/lm/clusters/").mock(
        return_value=httpx.Response(
            httpx.codes.CREATED,
            json={
                "id": 1,
                "name": "Cluster 1",
                "client_id": "cluster1",
                "configurations": [],
                "jobs": [],
            },
        ),
    )

    test_app = make_test_app("create", create)
    mocked_terminal_message = mocker.patch("lm_cli.subapps.clusters.terminal_message")
    result = cli_runner.invoke(
        test_app,
        shlex.split(
            unwrap(
                """
                create --name 'Cluster 1' --client-id 'cluster1'
                """
            )
        ),
    )

    assert result.exit_code == 0, f"create failed: {result.stdout}"
    assert create_route.called

    mocked_terminal_message.assert_called_once_with(
        "The cluster was created successfully.",
        subject="Cluster creation succeeded.",
    )


def test_delete__success(respx_mock, make_test_app, dummy_domain, cli_runner, mocker):
    """
    Test if the delete command makes the request to delete the cluster by id.
    """
    delete_route = respx_mock.delete(f"{dummy_domain}/lm/clusters/1").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            json={"message": "Cluster deleted successfully."},
        )
    )

    test_app = make_test_app("delete", delete)
    mocked_terminal_message = mocker.patch("lm_cli.subapps.clusters.terminal_message")
    result = cli_runner.invoke(test_app, shlex.split("delete --id=1"))

    assert result.exit_code == 0, f"delete failed: {result.stdout}"
    assert delete_route.called

    mocked_terminal_message.assert_called_once_with(
        "The cluster was deleted successfully.",
        subject="Cluster delete succeeded",
    )
