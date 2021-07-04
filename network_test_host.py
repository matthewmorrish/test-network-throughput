"""

Test network transmission rate - host

Matthew Morrish

"""


# Imports
import socket, os


# Set vars
host   = '192.168.1.234'
port   = 5005
buffer = 32


# Parse received packet & return a byte-literal of requested size
def genReturnPacket(data):
    data = data.decode('utf-8').strip("'").split(';')[1].split(':')
    size = 1024 ** {'b': 0, 'kib': 1, 'mib': 2, 'gib': 3}[data[1]] * int(data[0])

    print(f'Received request for: {data[0]}{data[1]}')
    return os.urandom(size)


# Main loop
def main():
    while 1:
        # Build socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(1)

        try:
            # Connect to client, collect packet, reply
            conn, _ = s.accept()
            data = conn.recv(buffer)
            conn.sendall(genReturnPacket(data))

        # In-case our socket fails
        except Exception as e:
            # print(type(e), e)
            conn.close()


if __name__ == '__main__':
    main()