#!/usr/bin/env python3

"""

Host

Test local network transmission rate for non-traditional python-specific
databases that utilize the TCP protocol of the socket library.

Usage:
    python3 network_test_host.py [optional flags] ...

Matthew Morrish

"""


# Imports
import argparse, socket
from sys import platform
from os import urandom, popen
from subprocess import check_output


# Set vars
buffer = 32 # Don't touch, must match client request len


# Get args
parser = argparse.ArgumentParser()
parser.add_argument(
    '-ip',  '--hostip', help='Manually set host machines IP address, default is automatically detected', 
    type=str, nargs='?', const=1, default=socket.gethostbyname(socket.gethostname()))
parser.add_argument(
    '-p',  '--port', help='Port, default is 5005', 
    type=int, nargs='?', const=1, default=5005)
parser.add_argument(
    '-mb',  '--membuffer', help='Percent of memory to be left unused during peak memory usage, default is 10', 
    type=int, nargs='?', const=1, default=10)
parser.add_argument(
    '-c',  '--continuous', help='When set the program will reset state and rerun after each test', 
    action='store_true')
parser.add_argument(
    '-v',  '--verbose', help='Provides additional information during runtime', 
    action='store_true')
args = parser.parse_args()


# Set global var for transfer data
response_li = []


# Quality-of-life
getSize   = lambda unit, multiplier : 1024 ** {'b': 0, 'kib': 1, 'mib': 2, 'gib': 3}[unit] * int(multiplier)
parseData = lambda data : data.decode('utf-8').strip("'").split(';')[1].split(':')
vPrint    = print if args.verbose else lambda *a, **k: None


# Check to see if the system has sufficient memory
def checkMem(unit, multiplier, cycles):
    req = getSize(unit, multiplier) * int(cycles)

    if platform == 'linux' or platform == 'linux2':
        _, _, avail_mem = map(int, popen('free -t -m').readlines()[-1].split()[1:]) # In MiB
        avail_mem = int(avail_mem) * 1024 * 1024 # Convert to B

    elif platform == 'win32':
        avail_mem = check_output('wmic OS get FreePhysicalMemory').decode('utf-8')
        avail_mem = ''.join(ch for ch in avail_mem if ch.isdigit()) # In KiB
        avail_mem = int(avail_mem) * 1024 # Convert to B

    if avail_mem > req + req*(args.membuffer/100):
        return True


# Main loop
def main():
    global response_li

    vPrint(f'\nHost: Running on {args.hostip}:{args.port}...')

    while 1:
        # Build socket & wait
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((args.hostip, args.port))
        s.listen(1)

        try:
            # Connect to client, collect & parse request packet
            conn, addr = s.accept()
            data = parseData(conn.recv(buffer))

            # Handle for init request, update user
            if data[0] == '0':
                vPrint(f'Host: Received new test request from [{addr[0]}] for [{data[1]}] cycles of [{data[2]} {data[3]}]')

                # Empty possible remainders in-case a test was interrupted, update user
                response_li = []
                vPrint('Host: Memory self-test ', end='')

                # Self-test memory capacity
                if checkMem(data[3], data[2], data[1]):
                    vPrint('[PASSED]\n...')

                    # Generate a list of byte-literals of requested size & reply sys status good
                    response_li = [urandom(getSize(data[3], data[2])) for _ in range(int(data[1]))]
                    conn.sendall(b'00000000000000;self_test_pass')

                # Reply sys status bad
                else:
                    vPrint('[FAILED]')
                    conn.sendall(b'00000000000000;self_test_fail')

            # If not initial request, send test data
            else:
                vPrint(f'Host: Replying to request [{data[0]}/{data[1]}]')
                conn.sendall(response_li.pop())
                vPrint(f'      [{len(response_li)}] items remaining in memory...')

        # In-case our socket fails
        except socket.error as e:
            vPrint(f'Host: Failed... {e}')
            conn.close()

        # End if continuous arg isn't set
        if not response_li and not args.continuous:
            break


if __name__ == '__main__':
    main()