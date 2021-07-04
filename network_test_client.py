"""

Test network transmission rate - client

Matthew Morrish

"""


# Imports
import socket, time


# Set vars
host        = '192.168.1.234'
port        = 5005
request_len = 32

unit       = 'mib'
multiplier = 100
cycles     = 10
response_len = 1024 ** {'b': 0, 'kib': 1, 'mib': 2, 'gib': 3}[unit] * multiplier


# Transfers 'msg' to host while timing cycle
def transfer(msg):
    try:
        # Build socket & connect to host
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))

        # Start timer & send
        core_start = time.perf_counter()
        s.sendall(msg)

        # Receive & end timer
        response = s.recv(response_len)
        core_time = time.perf_counter()-core_start

        # Close socket & return core-time, size of data received (in bytes)
        s.close()
        return core_time, len(response)

    # In-case our socket fails
    except Exception as e:
        raise Exception(f'Connection to [{host}] on port [{port}] failed... More Info [{e}]')


def main():

    # Prep & pad message (32-byte padding is 3-byte offset to account for b'')
    msg = ';' + str(multiplier) + ':' + str(unit)
    msg = msg.zfill(request_len-3)
    msg = msg.encode()
    
    # To get avg
    core_total, core_rate_total = 0, 0

    # Run loop
    for i in range(1, cycles+1):

        cycle_data = transfer(msg)

        core_total      += cycle_data[0]
        core_rate        = cycle_data[1] / cycle_data[0]
        core_rate_total += core_rate

        # Update user on the cycle
        print(f'Cycle {i}/{cycles}:\n', 
              f'   Time: {cycle_data[0]}(s)\n',
              f'   Recvd Data Size: {cycle_data[1]} Bytes\n',
              f'   Transfer Rate: {cycle_data[1]/cycle_data[0]} Bytes/(s)\n')

    # Update user on the average
    print(f'Final Results:\n',
          f'    Avg Time: {round(core_total/cycles, 4)}(s)\n',
          f'    Avg Transfer Rate: {core_rate_total/cycles} Bytes/(s)\n')


if __name__ == '__main__':
    main()