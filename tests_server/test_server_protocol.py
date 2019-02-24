from unittest.mock import patch, MagicMock
from pytest import fixture
from twisted.test.proto_helpers import StringTransport
from server_pkg.protocol import create_server, SyncFactory


@patch("server_pkg.protocol.reactor")
@patch("server_pkg.protocol.SyncFactory")
@patch("server_pkg.protocol.TCP4ServerEndpoint")
def test_connect(endpoint_mock, factory_mock, reactor_mock):

    reactor = create_server("/var/log", 9999)

    endpoint_mock.assert_called_once_with(reactor_mock, 9999)
    factory_mock.assert_called_once_with("/var/log")
    endpoint_mock.return_value.listen.assert_called_once_with(factory_mock.return_value)

    assert reactor == reactor_mock, "Incorrect reactor reference returned"


def test_protocol(setup_connection):

    factory, protocol1, transport1 = setup_connection

    assert protocol1.factory == factory, "Incorrect protocol creation"
    assert protocol1.delimiter == b"\r\r\r\n\n\n", "Incorrect protocol delimiter"
    assert protocol1.connected, "Protocol didn't connect properly"
    assert factory.connection_made, "Factory flag has not been set on first connection"

    protocol2 = factory.buildProtocol("127.0.0.1")
    transport2 = StringTransport()
    protocol2.makeConnection(transport2)
    assert transport2.disconnected, "Protocol connection must be refused when a second client is connected"

    assert factory.connection_made, "Factory flag mustn't change when a connection is aborted for a second client"


@patch("server_pkg.protocol.os")
def test_created_event(os_mock, setup_connection):

    factory, protocol, transport1 = setup_connection

    # test for folder
    protocol.lineReceived(b"created::1::./tests")
    os_mock.makedirs.assert_called_with("/var/log/tests", exist_ok=True)

    # test for file
    os_mock.path.exists.return_value = False
    os_mock.path.dirname.return_value = "/var/log/testing"
    protocol.lineReceived(b"created::0::./testing/test.log")
    os_mock.path.exists.assert_any_call("/var/log/testing/test.log")
    os_mock.path.dirname.assert_called_with("/var/log/testing/test.log")
    os_mock.path.exists.assert_called_with("/var/log/testing")
    os_mock.makedirs.assert_called_with("/var/log/testing", exist_ok=True)
    os_mock.mknod.assert_called_with("/var/log/testing/test.log")


@patch("server_pkg.protocol.shutil")
@patch("server_pkg.protocol.os")
def test_deleted_event(os_mock, shutil_mock, setup_connection):

    factory, protocol, transport1 = setup_connection

    # test for folder
    protocol.lineReceived(b"deleted::1::./tests")
    shutil_mock.rmtree.assert_called_with("/var/log/tests", ignore_errors=True)

    # test for file
    os_mock.path.exists.return_value = True
    protocol.lineReceived(b"deleted::0::./tests/test.log")
    os_mock.path.exists.assert_called_with("/var/log/tests/test.log")
    os_mock.remove.assert_called_with("/var/log/tests/test.log")


@patch("server_pkg.protocol.shutil")
@patch("server_pkg.protocol.os")
def test_moved_event(os_mock, shutil_mock, setup_connection):

    factory, protocol, transport1 = setup_connection

    # test for folder
    os_mock.path.exists.return_value = True
    protocol.lineReceived(b"moved::1::./tests::./testing")
    os_mock.path.exists.assert_called_with("/var/log/tests")
    shutil_mock.move.assert_called_with("/var/log/tests", "/var/log/testing")

    # test for file
    os_mock.path.exists.return_value = True
    protocol.lineReceived(b"moved::1::./tests.log::./testing.log")
    os_mock.path.exists.assert_called_with("/var/log/tests.log")
    shutil_mock.move.assert_called_with("/var/log/tests.log", "/var/log/testing.log")


@patch("server_pkg.protocol.open")
def test_modify_event(open_mock, setup_connection):

    factory, protocol, transport1 = setup_connection

    fh = MagicMock()
    open_mock.return_value = fh
    protocol.lineReceived(b"modified::0::./tests.log::Test content.")
    open_mock.assert_called_with("/var/log/tests.log", "wb")
    fh.__enter__.return_value.write.assert_called_with(b"Test content.")


@fixture(scope='module')
def setup_connection():

    print("\nInitialising factory and protocol objects\n")

    factory = SyncFactory("/var/log")

    assert factory.sync_folder == "/var/log", "Incorrect initialisation"
    assert not factory.connection_made, "Incorect initialisation"

    protocol = factory.buildProtocol("127.0.0.1")
    transport = StringTransport()
    protocol.makeConnection(transport)

    return factory, protocol, transport
