import logging
import os
import shutil
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor


class SyncServerProtocol(LineReceiver):
    """
    A custom protocol built on top of the LineReceiver protocol - messages are buffered until a delimiter (\r\r\r\n\n\n) is received.
    """

    delimiter = b"\r\r\r\n\n\n"

    MAX_LENGTH = 999999999

    def __init__(self, factory):
        """
        Initialise the protocol object.

        :param factory: reference to the factory
        """

        super().__init__()

        self.factory = factory

    def connectionMade(self):
        """
        Called when the connection is established - abort if another client has already connected.
        """

        # check if a connection with another client has already been made
        if self.factory.connection_made:
            self.transport.abortConnection()
            logging.warning(f"Connection with {self.transport.getPeer().host} has been aborted.")
        else:
            self.factory.connection_made = True
            logging.info(f"Connection with {self.transport.getPeer().host} has been established.")

    def connectionLost(self, reason):
        """
        Called when the connection is lost.

        :param reason: the reason as reported by twisted.
        """

        print("LOSING")
        self.factory.connection_made = False
        logging.warning(f"Connection with {self.transport.getPeer().host} has been lost - {reason}.")

    def lineReceived(self, line):
        """
        Called when the full message was received.

        :param line: the sent message
        """

        logging.info(f"Received {line}")

        # messages follow the format <event_type>::<flag for directory event>::<msg body dependent on event>
        msg_parts = line.split(b"::", 2)

        if len(msg_parts) != 3:
            logging.info(f"Protocol violation - {msg_parts}")
            return

        msg_type = msg_parts[0].decode("utf-8")
        is_directory = bool(int(msg_parts[1].decode("utf-8")))
        msg_body = msg_parts[2]

        handle_method = f"handle_{msg_type}"
        try:
            getattr(self, handle_method)(is_directory, msg_body)
        except AttributeError as e:
            logging.info(f"Received unrecognized message type - {msg_type} - {e}")

    def handle_created(self, is_directory, event_path):
        """
        Called when a 'created' event is received.

        :param is_directory: True if event is for a directory and False otherwise (bool)
        :param event_path: the message body is simply the path of the created folder/file (bytes)
        """

        abs_path = f"{self.factory.sync_folder}{event_path[1:].decode('utf-8')}"
        logging.info(f"Creating {'directory' if is_directory else 'file'} {abs_path}")

        if is_directory:
            # recursively create all the folders in the path
            os.makedirs(abs_path, exist_ok=True)
        else:
            # check if the file exists already
            if not os.path.exists(abs_path):

                # check if for some reason the base directory of the new file do not exist
                base_folder = os.path.dirname(abs_path)
                if not os.path.exists(base_folder):
                    os.makedirs(base_folder, exist_ok=True)

                # create the new file
                os.mknod(abs_path)

    def handle_deleted(self, is_directory, event_path):
        """
        Called when a 'deleted' event is received.

        :param is_directory: True if event is for a directory and False otherwise (bool)
        :param event_path: the message body is simply the path of the deleted folder/file (bytes)
        :return:
        """

        # build up the absolute path to delete
        abs_path = f"{self.factory.sync_folder}{event_path[1:].decode('utf-8')}"
        logging.info(f"Deleting {'directory' if is_directory else 'file'} {abs_path}")

        # if deleting a directory, do a recursive delete
        if is_directory:
            shutil.rmtree(abs_path, ignore_errors=True)
        else:
            # if deleting a file check that it exists first
            if os.path.exists(abs_path):
                os.remove(abs_path)

    def handle_modified(self, is_directory, msg_body):
        """
        Called when a 'modified' event is received.

        :param is_directory: True if event is for a directory and False otherwise (bool)
        :param msg_body: the body of the message, follows format '<event path>::<modified content>' (bytes)
        :return:
        """

        if is_directory:
            return  # this shouldn't be received in the first place

        # retrieve path and content
        path, content = msg_body.split(b"::", 1)

        # build the absolute path to modify
        abs_path = f"{self.factory.sync_folder}{path[1:].decode('utf-8')}"
        logging.info(f"Modifying file {abs_path}")

        with open(abs_path, 'wb') as fh:
            fh.write(content)

    def handle_moved(self, is_directory, msg_body):
        """
        Called when a 'moved' event is received.

        :param is_directory: True if event is for a directory and False otherwise (bool)
        :param msg_body: the body of the message, follows format '<source path>::<destination path>'
        """

        src_path, dest_path = msg_body.decode("utf-8").split("::", 1)
        # build up the absolute paths for the event
        abs_src_path = f"{self.factory.sync_folder}{src_path[1:]}"
        abs_dest_path = f"{self.factory.sync_folder}{dest_path[1:]}"

        # make sure the source path exists before trying to move it
        if os.path.exists(abs_src_path):
            logging.info(f"Moving {'directory' if is_directory else 'file'} {abs_src_path} to {abs_dest_path}")
            shutil.move(abs_src_path, abs_dest_path)


class SyncFactory(Factory):
    """
    Protocol factory used to build protocol objects when a new connection is made.
    """

    def __init__(self, sync_folder_path):
        """
        Initialise the factory.

        :param sync_folder_path: the path of the folder to synchronise
        """

        self.sync_folder = sync_folder_path
        self.connection_made = False  # a flag if a connection with a client has been made

    def buildProtocol(self, addr):
        """
        Called to create a new protocol object for incoming connections.

        :param addr: connection address

        :return: new protocol object
        """

        return SyncServerProtocol(self)


def create_server(sync_folder_path, port=9876):
    """
    A function used to initialise the server TCP endpoint.

    :param sync_folder_path: folder to synchronise (string)
    :param port: port number (int) defaults to 9876

    :return: a reference to twisted's reactor
    """

    endpoint = TCP4ServerEndpoint(reactor, port)
    endpoint.listen(SyncFactory(sync_folder_path))

    return reactor
