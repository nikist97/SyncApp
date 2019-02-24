## Client-Server Synchronisation Application

The application is built using:

1) Python (only tested with 3.6)
2) Twisted (used for networking)
3) Watchdog (used to monitor folder for changes)
4) Pytest (used for testing)
5) Pipenv (used for managing virtual environments)

OS dependency:

1) The application has only been tested on Linux OS (Ubuntu distribution)

### Preparing a virtual environment

Before running the application it is recommended to use a Python virtual environment. If using pipenv,
run 

```
pipenv install
```

which should create a virtual environment with the necessary packages installed.
Otherwise, please use whatever way you prefer to create a virtual environment where the application will
be installed.

### Installing the application

In a virtual environment shell (assuming that the curent directory is the directory of the repository -
where **setup.py** is located), run

```
pip3 install .
```

### Running the tests

If pipenv was used to initialise a virtual environment, then pytest would have been installed, otherwise please
install pytest with:

```
pip3 install pytest
```

Then to run the tests simply execute the following command in the repository root folder:

```
pytest
```

### Running the application

The application runs on port 9876. Both the client and the server applications are configured to connect/listen
on this port number. Therefore, the server must have port 9876 opened and allowed by any firewall filters.

To run the client application from the repository root folder:

```
python3 client_pkg/client.py <absolute path of the folder to synchronise> <server IP address>
```

Example:

```
python3 client_pkg/client.py /home/ns/client_test_folder 127.0.0.1
```

To run the server application from the repository root folder:

```
python3 server_pkg/server.py <absolute path of the folder to synchronise>
```

Example:

```
python3 server_pkg/sever.py /home/ns/server_test_folder 
```
