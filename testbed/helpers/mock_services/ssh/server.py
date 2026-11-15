import socket


with socket.socket() as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 2222))
    server.listen()
    while True:
        connection, _ = server.accept()
        with connection:
            connection.sendall(b"SSH-2.0-testbed-fake-ssh\r\n")
            connection.recv(4096)
            connection.sendall(b"SSH connectivity verified\n")
