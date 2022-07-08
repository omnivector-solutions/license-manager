import pytest
import typer

from lm_cli.exceptions import Abort, handle_abort


@pytest.fixture
def dummy_exception():
    return RuntimeError("Detonate!")


@pytest.fixture
def dummy_handled_function(dummy_exception):
    @handle_abort
    def _wrapped(
        message: str = "Explosive Message",
        subject: str = "BOOM!",
        support: bool = True,
        log_message: str = "volatile log message",
        original_error: Exception = dummy_exception,
    ):
        raise Abort(
            message,
            subject=subject,
            support=support,
            log_message=log_message,
            original_error=original_error,
        )

    return _wrapped


def test_handle_abort__with_all_options(capsys, caplog, dummy_handled_function, dummy_exception):
    with pytest.raises(typer.Exit):
        dummy_handled_function()

    captured = capsys.readouterr()
    assert "Explosive Message" in captured.out
    assert "BOOM!" in captured.out
    assert "If the problem persists" in captured.out

    assert "volatile log message" in caplog.text
    assert f"Original exception: {dummy_exception}" in caplog.text


def test_handle_abort__does_not_log_if_log_message_and_original_error_are_None(caplog, dummy_handled_function):
    with pytest.raises(typer.Exit):
        dummy_handled_function(log_message=None, original_error=None)

    assert caplog.text == ""


def test_handle_abort__does_not_include_support_message_if_support_is_False(capsys, dummy_handled_function):
    with pytest.raises(typer.Exit):
        dummy_handled_function(support=False)

    captured = capsys.readouterr()
    assert "If the problem persists" not in captured.out


def test_handle_abort__does_not_include_subject_message_if_subject_is_None(mocker, dummy_handled_function):
    mocked_panel = mocker.patch("lm_cli.exceptions.Panel")
    with pytest.raises(typer.Exit):
        dummy_handled_function(message="Bang!", subject=None)

    assert mocked_panel.called_once_with("Bang!")
