import logging
from twisted.internet import reactor
from twisted.internet.protocol import Protocol
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol


class SyncClientProtocol(Protocol):
    """
    A custom protocol class used to handle the communication with the server.
    """

    def connectionMade(self):
        """
        Called when connection with the server is established.
        """

        logging.info(f"Connection has been established with {self.transport.getPeer().host}.")

    def connectionLost(self, reason):
        """
        Called when connection with the server is lost.

        :param reason: reason for losing the connection (string)
        """

        logging.warning(f"Connection with {self.transport.getPeer().host} has been lost - {reason}.")

        # stop the reactor since connection with server is lost
        reactor.stop()

    def send_event(self, event_type, is_directory, event_path):
        """
        Send a create/delete event to server.

        :param event_type: the type of the event (string)
        :param is_directory: True if the event was emitted for a directory and False if for a file (bool)
        :param event_path: the path of the directory/file of this event (string)
        """

        msg = f"{event_type}::{int(is_directory)}::{event_path}\r\r\r\n\n\n"
        self.send_message(msg)

    def send_modify_event(self, event_path, content):
        """
        Send a modify event to server - only valid for a file if its content was changed.

        :param event_path: the path of the directory/file of this event (string)
        :param content: the content of the modified file (bytes)
        """

        # build the message with concatenation, content is already in bytes
        msg = f"modified::0::{event_path}::".encode("utf-8") + content + b"\r\r\r\n\n\n"
        self.transport.write(msg)
        logging.info(f"Sending a modify message to server for file {event_path}")

    def send_move_event(self, is_directory, src_path, dst_path):
        """
        Sends an event for a folder/file being moved.

        :param is_directory: True if the event was emitted for a directory and False if for a file (bool)
        :param src_path: the source path, before the file was moved (string)
        :param dst_path: the destination path, after the file was moved (string)
        """

        msg = f"moved::{int(is_directory)}::{src_path}::{dst_path}\r\r\r\n\n\n"
        self.send_message(msg)

    def send_message(self, msg):
        """
        Utility method used to send a message to the server and handle encoding beforehand.

        :param msg: the message to send (string)
        """

        self.transport.write(msg.encode("utf-8"))
        logging.info(f"Sending message to server - {msg}")


def connect(connection_ip, connection_port=9876):
    """
    A function used to connect with the server.

    :param connection_ip: the IP address of the server (string)
    :param connection_port: the port number to connect to (int), defaults to 9876

    :return: a tuple of two values - a reference to the created protocol object and twisted's reactor
    """

    endpoint = TCP4ClientEndpoint(reactor, connection_ip, connection_port)
    protocol = SyncClientProtocol()
    connectProtocol(endpoint, protocol)  # returns a deferred object, use if callbacks are needed

    return protocol, reactor
