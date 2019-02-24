import sys
import logging
from client_pkg.monitoring import create_observer
from client_pkg.protocol import connect


# configure root logger with basic configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(thread)d - %(threadName)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


if __name__ == "__main__":

    assert len(sys.argv) == 3, "Expecting two arguments: python3 client.py <folder to synchronize> <server IP>"

    # retrieve arguments
    path = sys.argv[1]
    server_ip = sys.argv[2]

    # initialise the twisted reactor object and a protocol object used to communicate with the server
    protocol_instance, reactor = connect(server_ip)

    # create the watchdog observer object and start monitoring for changes
    observer = create_observer(protocol_instance, path)
    observer.start()  # starts the observer in a new thread

    # start the reactor's event loop, runs in the main thread
    reactor.run()
