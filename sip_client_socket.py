#!/usr/bin/env python

import socket

TCP_IP = '172.16.0.35'
TCP_PORT = 5060
BUFFER_SIZE = 1024
MESSAGE = """INVITE sip:uac@172.16.2.1:5060 SIP/2.0
Via: SIP/2.0/tcp 172.16.0.4:59825;branch=z9hG4bK-16003-1-0
From: sipp <sip:sipp@11.0.0.3:59825>;tag=16003SIPpTag001
To: uac <sip:uac@172.16.2.1:5060>
Call-ID: 1-16003@11.0.0.3
CSeq: 1 INVITE
Contact: sip:sipp@11.0.0.3:59825
Max-Forwards: 70
Subject: Performance Test
Content-Type: application/sdp
Content-Length: 127
Refer-To: <sip:refertarget@11.0.0.3>
Referred-By: <sip:referrer@11.0.0.3:59825>
Record-Route: <sip:11.0.0.3;lr>
Route: <sip:11.0.0.3;lr>

v=0
o=user1 53655765 2353687637 IN IP4 11.0.0.3
s=-
c=IN IP4 11.0.0.3
t=0 0
m=audio 8000 RTP/AVP 0
a=rtpmap:0 PCMU/8000"""

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
s.send(MESSAGE.encode())
data = s.recv(BUFFER_SIZE)
s.close()