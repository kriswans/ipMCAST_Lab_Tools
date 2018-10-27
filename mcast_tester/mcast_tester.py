import struct
import time
import sys
import os
import socket

def RX(LOGMSG_GRP,LOGMSG_PORT,decode=False):
    """

    """
    print("Starting Rx Process...\n")


    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', LOGMSG_PORT))  # use LOGMSG_GRP instead of '' to listen only
                                 # to LOGMSG_GRP, not all groups on LOGMSG_PORT
    mreq = struct.pack("4sl", socket.inet_aton(LOGMSG_GRP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    i=0
    j=0
    tl=[]
    avg=[]
    limit=100
    while True:
        rx_msg=sock.recv(2048)
        rx_msg=rx_msg.decode()
        payloadsize=len(rx_msg)
        len_packet=payloadsize+28
        if decode == True :
            rx_msg=rx_msg.decode()
            print(rx_msg)
        while True:
            i+=1
            rx_msg=sock.recv(2048)

            if i%limit==0:
                rx_msg=rx_msg.decode()
                payloadsize=len(rx_msg)
                len_packet=payloadsize+28
                t=time.time()
                tl.append(t)
                if j > 0 :
                    d=tl[j]-tl[j-1]
                    x=(limit/d)*len_packet*8
                    avg.append(x)
                j+=1

            if (i%(20*limit))==0:
                avg_Mbps=(sum(avg)/len(avg))/1000000
                print(str(avg_Mbps)+" is the average Mbps recieved for this entire test run.")
            if (i%(200*limit))==0 :
                if len(avg) > 11:
                    last_5_sample_avg=(sum(avg[-11:-1])/len(avg[-11:-1]))/1000000
                    print('\n\n\n'+str(last_5_sample_avg)+" is the average recieved Mbps of last 10 samples.\n\n\n")
            if decode == True :
                rx_msg=rx_msg.decode()
                print(rx_msg)


def TX(LOGMSG_GRP,LOGMSG_PORT,test,packetsize,limit,pause,message=None):


    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
    hostname=socket.gethostname()
    if message != None:
        message=bytes(hostname+' >> '+message,'utf-8')
        sock.sendto(message, (LOGMSG_GRP, LOGMSG_PORT))
    elif test == True:
        i=0
        j=0
        tl=[]
        avg=[]
        while True:
            pattern=bytes(payloadsize*('a'),'utf-8')
            sock.sendto(pattern, (LOGMSG_GRP, LOGMSG_PORT))
            if i%limit==0:
                time.sleep(pause)
                t=time.time()
                tl.append(t)
                if i > 0:
                    d=tl[j]-tl[j-1]
                    x=(limit/d)*payloadsize*8
                    j+=1
                    avg.append(x)
            i+=1
            if (i%(20*limit))==0:
                avg_Mbps=(sum(avg)/len(avg))/1000000
                print(str(avg_Mbps)+" is the average Mbps sent for this entire test run. "+str(i)+" total packets sent.")
            if (i%(200*limit))==0 :
                if len(avg) > 11:
                    last_5_sample_avg=(sum(avg[-101:-1])/len(avg[-101:-1]))/1000000
                    print('\n\n\n'+str(last_5_sample_avg)+" is the average sent Mbps of last 100 samples.\n\n\n")

    else:
        message=bytes("%s sent you a test to group %s on port %s"%(hostname,LOGMSG_GRP,LOGMSG_PORT),'utf-8')
        sock.sendto(message, (LOGMSG_GRP, LOGMSG_PORT))

if __name__=='__main__':
    vector=sys.argv[1]
    LOGMSG_GRP = sys.argv[2]
    LOGMSG_PORT = int(sys.argv[3])

    if vector == '-r':
        print("Listing on: "+str(sys.argv[2])+' port: '+str(sys.argv[3])+'\n')
        if '-d' in sys.argv:
            print("\nDecoding recieved messages\n")
            decode=True
            RX(LOGMSG_GRP,LOGMSG_PORT,decode)
        else:
            RX(LOGMSG_GRP,LOGMSG_PORT)


    elif vector == '-t':
        test=False
        if '-m' in sys.argv:
            m_idx=sys.argv.index('-m')
            message=sys.argv[m_idx+1]
            packetsize,limit,pause=(None,None,None)
            TX(LOGMSG_GRP,LOGMSG_PORT,test,packetsize,limit,pause,message)
        elif '-T' in sys.argv:
            test=True

            if '-p' in sys.argv:
                p_idx=sys.argv.index('-p')
                packetsize=int(sys.argv[p_idx+1])
                payloadsize=packetsize-28
            else:
                payloadsize=1472
            if '-l' in sys.argv:
                l_idx=sys.argv.index('-l')
                limit=int(sys.argv[l_idx+1])
            else:
                limit=100
            if '-P' in sys.argv:
                P_idx=sys.argv.index('-P')
                pause=float(sys.argv[P_idx+1])
            else:
                pause=.01

            TX(LOGMSG_GRP,LOGMSG_PORT,test,payloadsize,limit,pause)

        else:
            TX(LOGMSG_GRP,LOGMSG_PORT)
    else:
        sys.exit()
