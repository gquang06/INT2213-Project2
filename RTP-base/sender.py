import argparse
import socket
import sys

from utils import PacketHeader, compute_checksum  

time_out = 0.500

def sender(receiver_ip, receiver_port, window_size):
    # read input message
    message = sys.stdin.read()
    chunk_size = 1024
    chunk_data = []
    
    # split input message into sized chunks
    for i in range(0, len(message), chunk_size):
        if i < len(message) - chunk_size:
            chunk_data.append(message[i:i+chunk_size])
        else:
            chunk_data.append(message[i:len(message)])

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(time_out)

    seq_num = 0
    isConnected = False

    while not isConnected:

        pkt_header = PacketHeader(type=0, seq_num=seq_num, length=0)
        pkt_header.checksum = compute_checksum(pkt_header)
        s.sendto(bytes(pkt_header), (receiver_ip, receiver_port))
        
        try:
            pkt, _ = s.recvfrom(2048)
            pkt_header = PacketHeader(pkt[:16])
            if pkt_header.checksum == compute_checksum(pkt_header) and pkt_header.type == 3 and pkt_header.seq_num == 1:
                print("Connection established")
                isConnected = True
                seq_num = 1

        except socket.timeout:
            print("Connection timeout")

    base = seq_num

    while base <= len(chunk_data):
    
        for i in range(base, min(base + window_size, len(chunk_data) + 1)):

            payload = chunk_data[i - 1]
            pkt_header = PacketHeader(type=2, seq_num=i, length=len(payload))
            pkt_header.checksum = compute_checksum(pkt_header / payload)
            s.sendto(bytes(pkt_header / payload), (receiver_ip, receiver_port))
        
        try:
            while True:
                pkt, _ = s.recvfrom(2048)
                pkt_header = PacketHeader(pkt[:16])
                if (pkt_header.checksum == compute_checksum(pkt_header) 
                        and pkt_header.type == 3
                        and pkt_header.seq_num > base):
                    
                    base = pkt_header.seq_num

        except socket.timeout:
            print("ACK timeout, resending packets in window")

    isEndAck = False

    while not isEndAck:

        # send end packet
        pkt_header = PacketHeader(type=1, seq_num=base, length=0)
        pkt_header.checksum = compute_checksum(pkt_header)
        s.sendto(bytes(pkt_header), (receiver_ip, receiver_port))
        
        try:
            pkt, _ = s.recvfrom(2048)
            pkt_header = PacketHeader(pkt[:16])
            if (pkt_header.checksum == compute_checksum(pkt_header) 
                    and pkt_header.type == 3 
                    and pkt_header.seq_num == base + 1):

                print("Connection closed")
                isEndAck = True

        except socket.timeout:
            print("Connection timeout, resending end packet")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "receiver_ip", help="The IP address of the host that receiver is running on"
    )
    parser.add_argument(
        "receiver_port", type=int, help="The port number on which receiver is listening"
    )
    parser.add_argument(
        "window_size", type=int, help="Maximum number of outstanding packets"
    )
    args = parser.parse_args()

    sender(args.receiver_ip, args.receiver_port, args.window_size)


if __name__ == "__main__":
    main()
