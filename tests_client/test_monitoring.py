from unittest.mock import patch, Mock, MagicMock
from client_pkg.monitoring import create_observer, SyncEventHandler


@patch("client_pkg.monitoring.SyncEventHandler")
@patch("client_pkg.monitoring.Observer")
def test_observer_creation(observer_mock, handler_mock):

    observer = Mock()
    observer_mock.return_value = observer

    handler = Mock()
    handler_mock.return_value = handler

    protocol = object()  # used as a mock protocol object

    assert create_observer(protocol, "/var/log") == observer, "Incorrect observer reference returned."
    observer_mock.assert_called_once(), "Observer must have been created through its constructor."

    handler_mock.assert_called_once_with(protocol, "/var/log")
    observer.schedule.assert_called_once_with(handler, "/var/log", recursive=True)


@patch("client_pkg.monitoring.open")
@patch("client_pkg.monitoring.os.path.exists")
def test_event_handler(path_exists_mock, open_mock):

    protocol = Mock()

    handler = SyncEventHandler(protocol, "/var/log")
    assert handler.root_path == "/var/log", "Incorrect handler initialisation"
    assert handler.protocol == protocol, "Incorrect handler initialisation"

    # test created event
    event = Mock()
    setattr(event, "src_path", "/var/log/test/test.log")
    setattr(event, "is_directory", False)
    setattr(event, "event_type", "created")

    handler.on_created(event)
    protocol.send_event.assert_called_with("created", False, "./test/test.log")

    # test deleted event
    event = Mock()
    setattr(event, "src_path", "/var/log/test")
    setattr(event, "is_directory", True)
    setattr(event, "event_type", "deleted")

    handler.on_deleted(event)
    protocol.send_event.assert_called_with("deleted", True, "./test")

    # test modified event
    # test for directory
    event = Mock()
    setattr(event, "src_path", "/var/log/test")
    setattr(event, "is_directory", True)

    handler.on_modified(event)  # must return without reading anything (since the event is for a directory)

    # test modified for file
    event = Mock()
    setattr(event, "src_path", "/var/log/testing/test1.log")
    setattr(event, "is_directory", False)

    path_exists_mock.return_value = True

    file_mock = MagicMock()
    open_mock.return_value = file_mock
    file_mock.__enter__.return_value.read.return_value = b"This is a test"

    handler.on_modified(event)

    path_exists_mock.assert_called_once_with("/var/log/testing/test1.log")
    open_mock.assert_called_once_with("/var/log/testing/test1.log", "rb")
    protocol.send_modify_event.assert_called_with("./testing/test1.log", b"This is a test")

    # test moved event
    event = Mock()
    setattr(event, "src_path", "/var/log/test/test/test1")
    setattr(event, "dest_path", "/var/log/test/test/test2")
    setattr(event, "is_directory", True)

    handler.on_moved(event)
    protocol.send_move_event.assert_called_with(True, "./test/test/test1", "./test/test/test2")
