import sys
import logging
from server_pkg.protocol import create_server


# configure root logger with basic configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(thread)d - %(threadName)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

if __name__ == "__main__":

    assert len(sys.argv) == 2, "Expecting two arguments: python3 server.py <folder to synchronize>"

    # retrieve arguments
    path = sys.argv[1]

    reactor = create_server(path)  # create the server

    # start the reactor's event loop, runs in the main thread
    logging.info("Starting server")
    reactor.run()
