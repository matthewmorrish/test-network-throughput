"""

Test network transmission rate - host

Matthew Morrish

"""


# Imports
import socket
from os import urandom
from subprocess import check_output


# Set vars
host       = '192.168.1.234'
port       = 5005
buffer     = 32
mem_buffer = 0 # Percent


# Set global var for transfer data
response_li = []


# Quality-of-life
getSize   = lambda unit, multiplier : 1024 ** {'b': 0, 'kib': 1, 'mib': 2, 'gib': 3}[unit] * int(multiplier)
parseData = lambda data : data.decode('utf-8').strip("'").split(';')[1].split(':')


# Check to see if the system has sufficient memory (Windows)
def checkMemWin(unit, multiplier, cycles):
    req = getSize(unit, multiplier) * int(cycles)

    avail_mem = check_output('wmic OS get FreePhysicalMemory').decode('utf-8')
    avail_mem = ''.join(ch for ch in avail_mem if ch.isdigit()) # In KiB
    avail_mem = int(avail_mem) * 1024 # Convert to B

    if avail_mem > req + req*(mem_buffer/100):
        return True


# Main loop
def main():
    global response_li

    while 1:
        # Build socket & wait
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(1)

        try:
            # Connect to client, collect & parse request packet
            conn, addr = s.accept()
            data = parseData(conn.recv(buffer))

            # Handle for init request, update user
            if data[0] == '0':
                print(f'\nHost: Received new test request from [{addr[0]}] for [{data[1]}] cycles of [{data[2]} {data[3]}]')

                # Empty possible remainders in-case a test was interrupted, update user
                response_li = []
                print('Host: Memory self-test ', end='')

                # Self-test memory capacity
                if checkMemWin(data[3], data[2], data[1]):
                    print('[PASSED]\n...')

                    # Generate a list of byte-literals of requested size & reply sys status good
                    response_li = [urandom(getSize(data[3], data[2])) for _ in range(int(data[1]))]
                    conn.sendall(b'00000000000000;self_test_pass')

                # Reply sys status bad
                else:
                    print('[FAILED]')
                    conn.sendall(b'00000000000000;self_test_fail')

            # If not initial request, send test data
            else:
                print(f'Host: Replying to request [{data[0]}/{data[1]}]')
                conn.sendall(response_li.pop())
                print(f'      [{len(response_li)}] items remaining in memory...')

        # In-case our socket fails
        except Exception as e:
            #print(type(e), e)
            conn.close()


if __name__ == '__main__':
    main()