from unittest.mock import patch
from twisted.test.proto_helpers import StringTransport
from client_pkg.protocol import connect, SyncClientProtocol


@patch("client_pkg.protocol.reactor")
@patch("client_pkg.protocol.connectProtocol")
@patch("client_pkg.protocol.SyncClientProtocol")
@patch("client_pkg.protocol.TCP4ClientEndpoint")
def test_connect(endpoint_mock, protocol_mock, connect_protocol_mock, reactor_mock):

    protocol, reactor = connect("127.0.0.1", 9999)

    endpoint_mock.assert_called_once_with(reactor_mock, "127.0.0.1", 9999)
    protocol_mock.assert_called_once()
    connect_protocol_mock.assert_called_once_with(endpoint_mock.return_value, protocol_mock.return_value)

    assert protocol == protocol_mock.return_value, "Incorrect protocol reference returned"
    assert reactor == reactor_mock, "Incorrect reactor reference returned"


@patch("client_pkg.protocol.reactor")
def test_protocol(reactor_mock):

    protocol = SyncClientProtocol()
    transport = StringTransport()
    protocol.makeConnection(transport)

    # test send event - created or deleted
    # test for folder
    protocol.send_event("created", True, "./test")
    assert transport.value() == b"created::1::./test\r\r\r\n\n\n"
    transport.clear()

    # test for file
    protocol.send_event("deleted", False, "./test1.log")
    assert transport.value() == b"deleted::0::./test1.log\r\r\r\n\n\n"
    transport.clear()

    # test moved event
    # test for folder
    protocol.send_move_event(True, "./test1", "./test2")
    assert transport.value() == b"moved::1::./test1::./test2\r\r\r\n\n\n"
    transport.clear()

    # test for file
    protocol.send_move_event(False, "./test1.log", "./test2.log")
    assert transport.value() == b"moved::0::./test1.log::./test2.log\r\r\r\n\n\n"
    transport.clear()

    # test modify event
    protocol.send_modify_event("./test.log", b"Logging data for testing.")
    assert transport.value() == b"modified::0::./test.log::Logging data for testing.\r\r\r\n\n\n"
    transport.clear()

    # test connection lost
    protocol.connectionLost("test reason")
    reactor_mock.stop.assert_called_once()
