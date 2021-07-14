"""

Test network transmission rate - client

Matthew Morrish

"""


# Imports
import socket
from time import perf_counter


# Set vars
host        = '192.168.1.234'
port        = 5005
request_len = 32

unit       = 'mib' # !!! NEED A LIMITER THAT GOES UP TO THE PORTS MAXIMUM BUFFER SIZE
multiplier = 100
cycles     = 10
response_len = 1024 ** {'b': 0, 'kib': 1, 'mib': 2, 'gib': 3}[unit] * multiplier


# Make request to host while timing cycle
def transfer(msg):
    try:
        # Build socket & connect to host
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))

        # Start timer & send
        core_start = perf_counter()
        s.sendall(msg)

        # Receive & end timer
        response = s.recv(response_len)
        core_time = perf_counter()-core_start

        # Close socket & return core-time, data received
        s.close()
        return core_time, response

    # In-case our socket fails
    except Exception as e:
        return e


# Convert machine-readable to human-readable
def toHumanReadable(num):
    for unit in ['B', 'KiB', 'MiB']:
        if num < 1024.0:
            return f'{round(num, 3)} {unit}'
        num /= 1024.0
    return f'{round(num, 3)} GiB'


def main():
    # Make things more legible
    space_format = lambda curr, tot : ' ' * (len(str(tot)) - len(str(curr)) + 1)
    time_format  = lambda time : (str(time) + '0' * (7 - len(str(time))))[0:6]

    # Prep & pad request list (32-byte padding is 3-byte offset to account for b'')
    msg_li = [(';' + str(i) + ':' + str(cycles) + ':' + str(multiplier) + ':' + str(unit)).zfill(request_len-3).encode() for i in range(cycles+1)]

    # Update user
    print(f'\nRequesting [{toHumanReadable(response_len)}] from [{host}:{port}] with [{request_len} Bytes] of data: ', end='')

    # Make initial request
    init_results = transfer(msg_li.pop(0))

    # Handle for socket exceptions
    if isinstance(init_results, Exception):
        print(f'[FAILED]\n  {init_results}')

    else:
        # Parse results
        init_results = init_results[1].decode('utf-8').strip("'").split(';')[1]

        # Handle for host-side insufficient memory
        if init_results == 'self_test_fail':
            print('[FAILED]\n  Host self-test reported insufficient memory...')

        # Proceed with test
        elif init_results == 'self_test_pass':
            print('[PASS]')

            # Run loop
            core_time_total, received_total, failed, core_rate_li = 0, 0, 0, []
            for i in range(1, cycles+1):

                # Make request
                run_results = transfer(msg_li.pop(0))

                # Handle socket exceptions, update user
                if isinstance(run_results, Exception):
                    failed += 1
                    core_rate_li.append(0) # Patch so our final min/max always have something to work with

                    print(f'  Test{space_format(i, cycles)}[{i}/{cycles}]: Failed... {run_results}')

                else:
                    # Store results, update user
                    core_time_total += run_results[0]
                    received_total  += len(run_results[1])
                    core_rate        = len(run_results[1]) / run_results[0]
                    core_rate_li.append(core_rate)

                    print(f'  Test{space_format(i, cycles)}[{i}/{cycles}]:',
                          f'Time: [{time_format(run_results[0])}(s)], Bytes Received: [{toHumanReadable(len(run_results[1]))}]')

            # Update user on final results
            print(f'\nResponse statistics for [{host}]:\n',
                  f'  Received: [{cycles-failed}],',
                  f'Lost: [{failed} - {round((1-received_total/(response_len*cycles))*100, 2)}% loss]',
                  f'\nAverage response rate ([{request_len} Byte] request inclusive):\n',
                  f'  Minimum: [{toHumanReadable(min(core_rate_li))}/(s)],',
                  f'Maximum: [{toHumanReadable(max(core_rate_li))}/(s)],',
                  f'Average: [{toHumanReadable(sum(core_rate_li) / len(core_rate_li))}/(s)]\n')


if __name__ == '__main__':
    main()