import logging
import os
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class SyncEventHandler(FileSystemEventHandler):
    """
    A custom event handler for monitoring folder/file changes.
    """

    def __init__(self, protocol_instance, root_path):
        """
        Initialise the event handler.

        :param protocol_instance: reference to the protocol object used to communicate with server
        :param root_path: the path of the folder that's being monitored
        """

        self.protocol = protocol_instance
        self.root_path = root_path

    def on_any_event(self, event):
        """
        Called when an event is received, regardless of the type of the event.

        :param event: referene to the watchdog event object
        """

        logging.info(f"New event - {event.event_type} - {'directory' if event.is_directory else 'file'} - {event.src_path}")

    def on_created(self, event):
        """
        Called when a 'created' event is emitted.

        :param event: reference to the watchdog event object
        """

        # the absolute path of the event file/folder
        abs_path = event.src_path
        # replace the root path with a '.' to build a relative path to be sent to server
        relative_event_path = abs_path.replace(self.root_path, ".")

        # retrieve event type and the flag for directory/folder
        event_type = event.event_type
        is_directory = event.is_directory

        # only propagate changes if there is a connection with the server
        if self.protocol.connected:
            self.protocol.send_event(event_type, is_directory, relative_event_path)
        else:
            logging.warning("Connection with server has not been established, 'create' changes will not be propagated.")

    def on_deleted(self, event):
        """
        Called when a 'deleted' event is emitted.

        :param event: reference to the watchdog event object
        """

        # the absolute path of the event file/folder
        abs_path = event.src_path
        # replace the root path with a '.' to build a relative path to be sent to server
        relative_event_path = abs_path.replace(self.root_path, ".")

        # retrieve event type and the flag for directory/folder
        event_type = event.event_type
        is_directory = event.is_directory

        # only propagate changes if there is a connection with the server
        if self.protocol.connected:
            self.protocol.send_event(event_type, is_directory, relative_event_path)
        else:
            logging.info("Connection with server has not been established, 'delete' changes will not be propagated.")

    def on_modified(self, event):
        """
        Called when a 'modified' event is emitted.

        :param event: reference to the watchdog event object
        """

        # the absolute path of the event file/folder
        abs_path = event.src_path
        # replace the root path with a '.' to build a relative path to be sent to server
        relative_event_path = abs_path.replace(self.root_path, ".")

        # retrieve the flag for directory/folder
        is_directory = event.is_directory

        # modified events are emitted for folders if something inside them has changed, do not propagate these to server
        if is_directory:
            logging.info(f"Modified events for directories are not propagated to server.")
            return

        # make sure the file exists
        if os.path.exists(abs_path):

            # read the file content
            with open(abs_path, "rb") as fh:
                content = fh.read()

            # if server connection is established propagate the content of the modified file
            if self.protocol.connected:
                self.protocol.send_modify_event(relative_event_path, content)
            else:
                logging.info("Connection with server has not been established, changes will not be propagated.")
        else:
            logging.info(f"Received a modified event even though the event file does not exist - {abs_path}")

    def on_moved(self, event):
        """
        Called when a 'moved' event is emitted.

        :param event: reference to the watchdog event object
        """

        # build the relative source and destination paths
        source_path = event.src_path.replace(self.root_path, ".")
        destination_path = event.dest_path.replace(self.root_path, '.')
        is_directory = event.is_directory

        # propagate the moved event if server connection is established
        if self.protocol.connected:
            self.protocol.send_move_event(is_directory, source_path, destination_path)
        else:
            logging.info("Connection with server has not been established, changes will not be propagated.")


def create_observer(protocol_instance, path):
    """
    A function used to initialise the event handler and the observer.

    :param protocol_instance: reference to protocol object used to communicate with server
    :param path: the path of the folder to monitor

    :return: a reference to the created observer
    """

    observer = Observer()
    # schedule a recursive observer, so that everything is monitored
    observer.schedule(SyncEventHandler(protocol_instance, path), path, recursive=True)

    return observer
