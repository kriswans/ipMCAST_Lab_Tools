import struct
import time
import sys
import os
import socket
from ipaddress import ip_address as ip
from pprint import pprint as pp


def RX(LOGMSG_GRP,LOGMSG_PORT,decode=False):

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
    counter_list=[]
    loss_list=[]
    packets=100
    while True:
        rx_msg=sock.recv(2048)
        rx_msg=rx_msg.decode()
        if decode == True :
            print(rx_msg)
        if decode==False:
            counter=int(rx_msg[0:12])
            counter_list.append(counter)
            payloadsize=len(rx_msg)
            len_packet=payloadsize+28

        while True:
            i+=1
            rx_msg=sock.recv(2048)
            if decode == True :
                rx_msg=rx_msg.decode()
                print(rx_msg)
            if decode == False:
                counter=int(rx_msg[0:12])
                counter_list.append(counter)
                packet_delta=counter_list[i]-counter_list[i-1]
                if packet_delta <= 0:
                    print("\nEither new Tx test run has occured or packets have been recieved out-of-order. Please restart reciever, then sender.\n")
                    sys.exit()

                loss=packet_delta-1
                loss_list.append(loss)

                if i%packets==0:
                    rx_msg=rx_msg.decode()
                    payloadsize=len(rx_msg)
                    len_packet=payloadsize+28
                    t=time.time()
                    tl.append(t)
                    if j > 0 :
                        d=tl[j]-tl[j-1]
                        try:
                            x=(packets/d)*len_packet*8
                            avg.append(x)
                        except:
                            print('Overrun! Send less traffic.')
                            sys.exit()
                    j+=1

                if (i%(20*packets))==0:
                    avg_Mbps=(sum(avg)/len(avg))/1000000
                    print(str(avg_Mbps)+" is the average Mbps recieved for this entire test run.\n")
                    avg_loss=(sum(loss_list)/len(loss_list))*100
                    print(str(avg_loss)+"% is the percent packet loss for the entire test run.\n")
                    total_loss=sum(loss_list)
                    print(str(total_loss)+" is the total packet loss for the entire test run.\n")

                if (i%(200*packets))==0 :
                    if len(avg) > 11:
                        last_5_sample_avg=(sum(avg[-11:-1])/len(avg[-11:-1]))/1000000
                        print('\n\n\n'+str(last_5_sample_avg)+" is the average recieved Mbps of last 10 samples.\n\n\n")



def TX(LOGMSG_GRP,LOGMSG_PORT,test,packetsize,limit,pause,pts,message=None):


    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
    hostname=socket.gethostname()
    if message != None:
        message=bytes(hostname+' >> '+message,'utf-8')
        sock.sendto(message, (LOGMSG_GRP, LOGMSG_PORT))
    elif test == True:
        i=0
        j=0
        k=1
        tl=[]
        avg=[]
        payloadsize=packetsize-28
        while k <= pts:
            str_k=str(k)
            str_k=str_k.zfill(12)
            pattern=bytes(str_k+(payloadsize-12)*('a'),'utf-8')
            sock.sendto(pattern, (LOGMSG_GRP, LOGMSG_PORT))
            k+=1
            if i%limit==0:
                time.sleep(pause)
                t=time.time()
                tl.append(t)
                if i > 0:
                    d=tl[j]-tl[j-1]
                    x=(limit/d)*packetsize*8
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

def arg_parser(args):

    test=False
    packetsize=512
    payloadsize=packetsize-28
    limit=50
    pause=2
    pts=2000
    decode=False
    message=None

    if len(sys.argv) >=4:
        vector=sys.argv[1]
        if sys.argv[1] not in '-t-r':
            print("\nMust specify either -t for transmit or -r for recieve.\n")
            sys.exit()
        LOGMSG_GRP = sys.argv[2]
        try:
            is_mcast=ip(sys.argv[2]).is_multicast
            if is_mcast==False:
                print("\n%s is not a multicast address\n"%(sys.argv[2]))
                sys.exit()
        except:
            print("\nMust specify a correct IP address in dotted decimal format (x.x.x.x)\n")
            sys.exit()

        LOGMSG_PORT = int(sys.argv[3])

        if vector == '-r':
            print("Listing on: "+str(sys.argv[2])+' port: '+str(sys.argv[3])+'\n')
            if '-d' in sys.argv:
                print("\nDecoding recieved messages\n")
                decode=True
                return vector,LOGMSG_GRP,LOGMSG_PORT,test,packetsize,limit,pause,pts,message,decode
            else:
                return vector,LOGMSG_GRP,LOGMSG_PORT,test,packetsize,limit,pause,pts,message,decode


        elif vector == '-t':

            if '-m' in sys.argv:
                m_idx=sys.argv.index('-m')
                try:
                    message=sys.argv[m_idx+1]
                except:
                    print("Need to specify message after -m")
                    sys.exit()
                return vector,LOGMSG_GRP,LOGMSG_PORT,test,packetsize,limit,pause,pts,message,decode
            elif '-T' in sys.argv:
                test=True
                if '-p' in sys.argv:
                    p_idx=sys.argv.index('-p')
                    try:
                        packetsize=int(sys.argv[p_idx+1])
                        payloadsize=packetsize-28
                    except:
                        print("Need to specify packet size after -p")
                        sys.exit()
                else:
                    payloadsize=1472
                    packetsize=1500
                if '-l' in sys.argv:
                    l_idx=sys.argv.index('-l')
                    try:
                        limit=int(sys.argv[l_idx+1])
                    except:
                        print("Need to specify loop number after -l")
                        sys.exit()

                else:
                    limit=100
                if '-P' in sys.argv:
                    P_idx=sys.argv.index('-P')
                    try:
                        pause=float(sys.argv[P_idx+1])
                    except:
                        print("Need to specify time to pause between loops after -P")
                        sys.exit()
                else:
                    pause=1
                if '-s' in sys.argv:
                    s_idx=sys.argv.index('-s')
                    try:
                        pts=int(sys.argv[s_idx+1])
                    except:
                        print("Need to specify number of packets sent after -s")
                        sys.exit()
                else:
                    pts=2000

                return vector,LOGMSG_GRP,LOGMSG_PORT,test,packetsize,limit,pause,pts,message,decode

            else:
                test=True
                print("-m or -T transmit variable not specified. Defaulting to -T: %iB packetsize, %i packets per loop, %i seconds interloop pause, sending %i packets."%(payloadsize+28,limit,pause,pts))
                return vector,LOGMSG_GRP,LOGMSG_PORT,test,packetsize,limit,pause,pts,message,decode
    else:
        if '-h' in sys.argv:
            with open ('helpfile.txt', 'r') as hf:
                f=hf.readlines()
                for i in f:
                    i.rstrip('\n')
                    i.lstrip('\t')
                    print(i)

            sys.exit()
        else:
            print("Not enough arguments. Need to at least specify '-t'(TX) or '-r'(RX) IPv4 Multicast Address and Port.\n")
            vector=input('\nSpecify -t or -r: ')
            if vector not in '-t-r':
                vector='-t'
                print('No valid vector specified. Defaulting to -t\n')
            LOGMSG_GRP=input('\nIPv4 Multicast Address: ')
            LOGMSG_PORT=int(input('\nUDP Port: '))
            if vector == '-t':
                packetsize=int(input('\nPacket Size: '))
                pts=int(input('\nPackets to send: '))
            if vector == '-r':
                packetsize,pts=(None,None)
            limit=50
            pause=1
            test=True
            if vector == '-t':
                print("\n-m or -T transmit variable not specified. Defaulting to -T: %iB packetsize, %i packets per loop, %i seconds interloop pause, sending %i packets."%(packetsize,limit,pause,pts))
            return vector,LOGMSG_GRP,LOGMSG_PORT,test,packetsize,limit,pause,pts,message,decode


if __name__=='__main__':

    args=sys.argv
    vector,LOGMSG_GRP,LOGMSG_PORT,test,packetsize,limit,pause,pts,message,decode=arg_parser(sys.argv)
    if vector == '-r':
        RX(LOGMSG_GRP,LOGMSG_PORT,decode)
    if vector =='-t':
        TX(LOGMSG_GRP,LOGMSG_PORT,test,packetsize,limit,pause,pts,message)
    sys.exit()
