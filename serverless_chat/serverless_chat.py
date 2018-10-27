"""
Author: Kris Swanson, kriswans@cisco.com
The Program passes chat messages and text files, while keeping
presence state of active users.
Tested with Python 3.6.1 on WIN10
"""


import socket
import struct
import time
import sys
import multiprocessing
import datetime

"""
fn notifies of first entry into chatroom by looking for users not in list
"""

def NewUserNotify():
    userlist=[]
    MCAST_GRP = '224.1.1.8'
    MCAST_PORT = 5008
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', MCAST_PORT))  # use MCAST_GRP instead of '' to listen only
                                 # to MCAST_GRP, not all groups on MCAST_PORT
    mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)

    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    while True:
      list_user=sock.recv(10240)
      dcduser=list_user.decode("utf-8")
      if dcduser not in userlist:
        userlist.append(dcduser)
        print("{dcduser} has entered the chatroom for first time this session\n".format(dcduser=dcduser))

"""
fn listens for messages and updates chat log
"""

def MsgRx():
    print("Starting Rx Process...\n")
    MCAST_GRP = '224.1.1.8'
    MCAST_PORT = 5007
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', MCAST_PORT))  # use MCAST_GRP instead of '' to listen only
                                 # to MCAST_GRP, not all groups on MCAST_PORT
    mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    pwf=open('pwf','r')
    password=pwf.read()
    pwf.close()
    try:
        while True:
          rx_msg=sock.recv(10240)
          dcdmsg=rx_msg.decode("utf-8")
          dcdmsg=bytes(dcdmsg,'ascii')
          DecryptMsg(dcdmsg,password)
    except:
        MsgRx()


"""
fn keeps track of the heartbeats generated by InfHBeat. It will then write the active, inactive, and total seen users
to a file that is printed during runtime using the #who command. 'sets' aree used to remove duplicate entries. inside
loop time is proportional to the length of active user list (userlist1).
"""

def UserTable():

        MCAST_GRP = '224.1.1.8'
        MCAST_PORT = 5008
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', MCAST_PORT))  # use MCAST_GRP instead of '' to listen only
                                     # to MCAST_GRP, not all groups on MCAST_PORT
        mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)

        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        userlist1=[]
        userlist=[]

        while True:
            if len(userlist1) > 0:
                who=open('who','w')
                ts = time.time()
                st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                who.write("Last updated: "+st+"\n")
                who.write("total users over time:\n")
                who.write(str(userlist)+"\n")
                who.write("active users:\n")
                who.write(str(userlist1)+"\n")
                who.write("users that have left (since you logged in):\n")
                who.write(str(list(set(userlist)-set(userlist1))))
                who.write("\n")
                who.close()
            i=0
            try:
                userlist1=[]
            except:
                pass
            while i < (len(userlist1)+1)*6:
                list_user=sock.recv(10240)
                dcduser=list_user.decode("utf-8")
                userlist.append(dcduser)
                userlist=set(userlist)
                userlist=list(userlist)
                userlist1.append(dcduser)
                userlist1=set(userlist1)
                userlist1=list(userlist1)
                i=i+1

"""
generates an infinite heartbeat consumed by UserTable
"""
def InfHBeat():
    user=open("localuser","r")
    user=user.read()
    ADV_GRP = '224.1.1.8'
    ADV_PORT = 5008

    hostname=(socket.gethostname())

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)

    while True:
        useradv=("{user}".format(user=user)+"@"+hostname)
        useradv=bytes(useradv, "ascii")
        sock.sendto(useradv, (ADV_GRP, ADV_PORT))
        time.sleep(5)


"""
Message encryption for Tx. Will be called from the MsgTx function before sending
"""
def EncryptMsg(msg,password):

    import base64
    import os
    from cryptography.fernet import Fernet
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    password = bytes(password,"ascii")
    try:
        saltf = open('salt','r')
        salt=saltf.read()
        salt=bytes(salt,"ascii")
        saltf.close()
    except:
        print("It appears there is no salt file.\n")
        salt_dec=input("Would you like to create one (Y) or manually import an existing file (N)")
        if salt_dec == 'Y':
            saltf = open('salt','w')
            salt = os.urandom(64)
            salt_st=str(salt)
            saltlen=len(salt_st)
            first=2
            last=saltlen-1
            salt_st=(salt_st[first:last])
            saltf.write(salt_st)
            saltf.close()

        else:
            print("Program exiting. Please include 'salt' file in the main program directory with the correct hash.")
            sys.exit()

    kdf = PBKDF2HMAC(
     algorithm=hashes.SHA256(),
     length=32,
     salt=salt,
     iterations=100000,
     backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    fk = Fernet(key)
    msg = fk.encrypt(msg)
    return msg

"""
Message decryption for Rx. Will be called from the MsgRx function after reciept.
"""

def DecryptMsg(dcdmsg,password):

    import base64
    import os
    from cryptography.fernet import Fernet
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    password = bytes(password,"ascii")
    try:
        saltf = open('salt','r')
        salt=saltf.read()
        salt=bytes(salt,"ascii")
        saltf.close()
    except:
        print("Recieved message and can't decode. It appears there is no salt file.\n")
        salt_dec=input("Would you like to create one (Y) or manually import an existing file (N)?:")
        if salt_dec == 'Y':
            saltf = open('salt','w')
            salt = os.urandom(64)
            salt_st=str(salt)
            saltlen=len(salt_st)
            first=2
            last=saltlen-1
            salt_st=(salt_st[first:last])
            saltf.write(salt_st)
            saltf.close()

        else:
            print("Program exiting. Please include 'salt' file in the main program directory with the correct hash.")
            sys.exit()

    kdf = PBKDF2HMAC(
     algorithm=hashes.SHA256(),
     length=32,
     salt=salt,
     iterations=100000,
     backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    fk = Fernet(key)
    try:
        dcdmsg = fk.decrypt(dcdmsg)
        dcdmsg = dcdmsg.decode("ascii")
        print(dcdmsg)
        chatlog=open("chatlog.log","a")
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        chatlog.write(dcdmsg+": "+st+"\n")
        chatlog.close()
    except:
        print("Invalid Encrypted or Unencrypted Message Recieved, can't decode")
        print("Peer salt file and passwords must match.")
        pass


"""
1. initializes who and chatlog files
2. sends messages
3. initializes processes
4. executes conditional commands
"""
def MsgTx(msg, user,password):
    MCAST_GRP = '224.1.1.8'
    MCAST_PORT = 5007

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
    print("Starting Tx process...\n")

    hostname=(socket.gethostname())

    who=open("who","w")
    who.write("populating table, please wait 30 seconds...")
    who.close()
    chatlog=open("chatlog.log","w")
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    chatlog.write("Chatlog started at :")
    chatlog.write(st)
    chatlog.write("\n")
    chatlog.close()

    jobs=[]

    z = multiprocessing.Process(target=InfHBeat)
    jobs.append(z)
    z.daemon = True
    z.start()

    n = multiprocessing.Process(target=UserTable)
    jobs.append(n)
    n.daemon = True
    n.start()

    o = multiprocessing.Process(target=NewUserNotify)
    jobs.append(o)
    o.daemon = True
    o.start()

    p = multiprocessing.Process(target=MsgRx)
    jobs.append(p)
    p.daemon = True
    p.start()


    while True:
        time.sleep(.5)
        while True:
            msg=input(": ")
            if msg == "#exit":
                user_d=("{user}".format(user=user)+"@"+hostname)
                left="{user} has left the chatroom".format(user=user_d)
                left=bytes(left,"ascii")
                sock.sendto(left, (MCAST_GRP, MCAST_PORT))
                sys.exit()
            if msg == "#who":
                who=open("who","r")
                for lines in who:
                    print(lines)
                break
            if msg == "#send":
                name=""
                name=input("Filename?: ")
                fn=open(name, "rb")
                for lines in fn:
                    lines=bytes(lines)
                    sock.sendto(lines, (MCAST_GRP, MCAST_PORT))
                fn.close()
                break
            if msg == "#help":
                hf=open("helpfile", "r")
                for lines in hf:
                    print(lines)
                hf.close()
                break
            if msg == "#log":
                cl=open("chatlog.log", "r")
                for lines in cl:
                    print(lines)
                cl.close()
                break


            else:
                hostname=(socket.gethostname())
                msg=user+'@'+hostname+"# "+'"'+msg+'"'
                msg=bytes(msg, "ascii")
                msg=EncryptMsg(msg,password)
                sock.sendto(msg, (MCAST_GRP, MCAST_PORT))


    sys.exit()
"""
main fn to pull user info and kick off MsgTx fn. MsgTx kicks off heartbeat and Rx functions.
"""

def main():

      print("Starting Chat Session\n")
      print("Type '#help' for list of commands\n")

      jobs = []
      msg=None

      user=input("Please enter your chat handle: ")
      localuser=open("localuser","w")
      localuser.write(user)
      localuser.close()
      password=input("Please enter your message encryption password: ")
      pwf=open('pwf','w')
      pwf.write(password)
      pwf.close()

      q = multiprocessing.Process(target=MsgTx(msg,user,password))
      jobs.append(q)
      q.start()


if __name__ == '__main__':
    main()