#!/bin/python

import glob
import argparse
import socket
import re
import sys
import os
from struct import *

parser = argparse.ArgumentParser()

# 'Internal_call__dir0__62067.pcap' to 
#
# Internal_call__dir0__62067.pcap__1.txt
# Internal_call__dir0__62067.pcap__2.txt
# Internal_call__dir0__62067.pcap__3.txt
parser.add_argument("-fname", help="input pcap filename", type=str, required=True)
parser.add_argument("-force", help="force to overwrite", type=bool, default=False)

args = parser.parse_args()

f = open(args.fname, mode='rb') 
data = f.read()
f.close()

directory = os.path.splitext(args.fname)[0]
if not os.path.exists(directory):
  os.makedirs(directory)
elif not args.force:
  sys.exit('error: directory \'%s\' already exists' % directory)

if len(data) <= 16:
  sys.exit('error: too short .pcap file')

# https://github.com/hokiespurs/velodyne-copter/wiki/PCAP-format

pcap_file_hdr = unpack('IHHiIII', data[0:24])
#print('.pcap file header: %x, %s' % (pcap_file_hdr[0], pcap_file_hdr[1:]))

if pcap_file_hdr[6] != 1:
  sys.exit('error: link layer header is not Ethernet. Did you captured this pcap file via "tcpdump -ni any"? ')


i = 24
file_num = 1
while i < len(data):
  pcap_pkt_hdr = unpack('IIII', data[i:i+16])
  if pcap_pkt_hdr[2] != pcap_pkt_hdr[3]:
    sys.exit('error: number of octets of packet saved in file (%d) != actual length of packet (%d)' % (pcap_pkt_hdr[2], pcap_pkt_hdr[3]))

  pcap_pkt_body_index = i+16

  eth_hdr = unpack('>12ch', data[pcap_pkt_body_index:pcap_pkt_body_index+14])

  eth_ipproto = eth_hdr[12]
  
  if eth_ipproto != 0x800:
    sys.exit('error: wrong eth proto: 0x%x' % eth_ipproto)

  #print(eth_hdr[0:6])
  #print(eth_hdr[6:12])

  pcap_pkt_body_index = pcap_pkt_body_index+14

  ip_hdr = unpack('=BBHHHBBHLL', data[pcap_pkt_body_index:pcap_pkt_body_index+20])
  ihl = ip_hdr[0] & 0x0F
  trans_proto = ip_hdr[6]
  ip_src = ip_hdr[8]
  ip_dst = ip_hdr[9]
  ip_hdr_total_len = socket.ntohs(ip_hdr[2])

  pcap_pkt_body_end = pcap_pkt_body_index + ip_hdr_total_len

  if trans_proto != 6:
    sys.exit('error: wrong transport proto: 0x%x, expected TCP' % eth_ipproto)

  pcap_pkt_body_index = pcap_pkt_body_index + ihl * 4

  tcp_hdr = unpack('>HHLLHHHH', data[pcap_pkt_body_index:pcap_pkt_body_index+20])
  tcp_hdr_len = (tcp_hdr[4] >> 12) * 4

  print('0x%x:%d => 0x%x:%d, iph_total: %s' % (ip_src, tcp_hdr[0], ip_dst, tcp_hdr[1], ip_hdr_total_len))

  pcap_pkt_body_index = pcap_pkt_body_index + tcp_hdr_len

  #print('*****%s*****' % data[pcap_pkt_body_index:pcap_pkt_body_end])

  # next pcap packet
  i = i + 16 + pcap_pkt_hdr[2]


  f = open(os.path.join(directory, '%s__%s.txt' % (args.fname, file_num)), 'w')
  f.write(data[pcap_pkt_body_index:pcap_pkt_body_end])
  f.close()

  file_num = file_num + 1