import argparse
import socket

from utils import PacketHeader, compute_checksum


def receiver(receiver_ip, receiver_port, window_size):

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((receiver_ip, receiver_port))

    expected_seq_num = 0
    isConnected = False
    
    while (isConnected == False):

        pkt, address = s.recvfrom(2048)
        pkt_header = PacketHeader(pkt[:16])

        if (pkt_header.checksum == compute_checksum(pkt_header) 
                and pkt_header.type == 0 
                and pkt_header.seq_num == 0):
            
            start_ack = PacketHeader(type=3, seq_num=1, length=0)
            start_ack.checksum = compute_checksum(start_ack)
            s.sendto(bytes(start_ack), address)
            expected_seq_num += 1
            isConnected = True
   
    while True:

        # Receive packet; address includes both IP and port
        pkt, address = s.recvfrom(2048)
        pkt_header = PacketHeader(pkt[:16])

        # Check for end packet
        if pkt_header.type == 1:

            end_ack = PacketHeader(type=3, seq_num=expected_seq_num+1, length=0)
            end_ack.checksum = compute_checksum(end_ack)
            s.sendto(bytes(end_ack), address)
            print("Connection closed")
            break

        # send ACK for received packet if it is not corrupted and in order
        if (pkt_header.checksum == compute_checksum(pkt_header) 
                and pkt_header.type == 2 
                and pkt_header.seq_num == expected_seq_num):
            
            msg = pkt[16 : 16 + pkt_header.length]
            print(msg.decode("utf-8"), end="")
            expected_seq_num += 1
            ack_pkt = PacketHeader(type=3, seq_num=expected_seq_num, length=0)
            ack_pkt.checksum = compute_checksum(ack_pkt)
            s.sendto(bytes(ack_pkt), address)

        # resend ACK for last in-order packet if received packet is out of order or corrupted
        else:
            ack_pkt = PacketHeader(type=3, seq_num=expected_seq_num, length=0)
            ack_pkt.checksum = compute_checksum(ack_pkt)
            s.sendto(bytes(ack_pkt), address)

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

    receiver(args.receiver_ip, args.receiver_port, args.window_size)


if __name__ == "__main__":
    main()
