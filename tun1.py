import fcntl,threading,os,struct,subprocess,socket,sys
from struct import *

TUNSETIFF = 0x400454ca
TUNSETOWNER = TUNSETIFF + 2
IFF_TUN = 0x0001
IFF_TAP = 0x0002
IFF_NO_PI = 0x1000

# Open TUN device file.
tun = open('/dev/net/tun', 'r+b')
# Tall it we want a TUN device named tun0.
ifr = struct.pack('16sH', 'asa0', IFF_TUN | IFF_NO_PI)
fcntl.ioctl(tun, TUNSETIFF, ifr)
# Optionally, we want it be accessed by the normal user.
fcntl.ioctl(tun, TUNSETOWNER, 1000)

# Bring it up and assign addresses.
subprocess.check_call('ifconfig asa0 10.0.1.1 pointopoint 10.0.1.2 up',
        shell=True)

#calculate checksum
def checksum(source_string):
    sum = 0
    countTo = (len(source_string)/2)*2
    count = 0
    while count<countTo:
        thisVal = ord(source_string[count + 1])*256 + ord(source_string[count])
        sum = sum + thisVal
        sum = sum & 0xffffffff 
        count = count + 2
    if countTo<len(source_string):
        sum = sum + ord(source_string[len(source_string) - 1])
        sum = sum & 0xffffffff 
    sum = (sum >> 16)  +  (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

tsock = socket.socket(socket.AF_INET,socket.SOCK_RAW,socket.IPPROTO_RAW)
stsock = socket.socket(socket.AF_PACKET,socket.SOCK_RAW, socket.htons(0x0800))

try :
	#capture incoming packet from physicle interface and write in TUN file Descriptor
	def recv_write_phyint():
		while True :
			rpacket=stsock.recvfrom(65565)
			rpacket = rpacket[0]
			rip_header=rpacket[14:34]
			iph = unpack('!BBHHHBBH4s4s' ,rip_header)
		
			tun_packet = rpacket[34:]
			tun_header=rpacket[34:54]
			tunh = unpack('!BBHHHBBH4s4s' ,tun_header)
	
			if socket.inet_ntoa(tunh[8]) == "10.0.1.2" :
					#write in descriptor
					os.write(tun.fileno(), tun_packet)
	thread_r_w = threading.Thread(target = recv_write_phyint)
	thread_r_w.daemon = True
	thread_r_w.start()

	while True:
	# Read an IP packet been sent to this TUN device.
    		recv_packet =str(os.read(tun.fileno(), 2048))
	#create new IP Header
		ip_ver_ihl=(4<<4)+5
		ip_tos=0
		ip_len=4069
		ip_id=0xc88f
		ip_flag=0
		ip_ttl=64
		ip_pro=1
		ip_check=0
		ip_src=socket.inet_aton("192.168.10.1")
		ip_des=socket.inet_aton("192.168.10.2")
		ip_header=struct.pack('!BBHHHBBH4s4s',ip_ver_ihl,ip_tos,ip_len,ip_id,ip_flag,ip_ttl,ip_pro,ip_check,ip_src,ip_des)
		packet = ip_header+recv_packet
		ip_check2=checksum(packet)
		ip_header2=struct.pack('!BBHHHBBH4s4s',ip_ver_ihl,ip_tos,ip_len,ip_id,ip_flag,ip_ttl,ip_pro,ip_check2,ip_src,ip_des)
		packet2 = ip_header2+recv_packet
	#send ping packet+new ip header	
		tsock.sendto(packet2 ,("192.168.10.2",0))
except KeyboardInterrupt :
		print "Closed!"




 
