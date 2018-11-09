import struct
import socket
import sys


def reflector_U_M(REF_D_IP,REF_D_PORT,REF_D_GRP):

    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.bind((REF_D_IP, REF_D_PORT))
    msock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    msock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)

    while True:
        data, addr = sock.recvfrom(2048)
        msock.sendto(data, (REF_D_GRP, REF_D_PORT))

if __name__=='__main__':
    REF_D_IP,REF_D_PORT,REF_D_GRP=(sys.argv[1],int(sys.argv[2]),sys.argv[3])
    reflector_U_M(REF_D_IP,REF_D_PORT,REF_D_GRP)
