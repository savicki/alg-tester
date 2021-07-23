#!/usr/bin/env python

import socket

TCP_IP = '172.16.2.3'
TCP_PORT = 5060
BUFFER_SIZE = 1024
MESSAGE = """INVITE sip:uac@172.16.2.1:5060 SIP/2.0\r
Via: SIP/2.0/tcp 172.16.0.4:59825;branch=z9hG4bK-16003-1-0\r
From: sipp <sip:sipp@11.0.0.3:59825>;tag=16003SIPpTag001\r
To: uac <sip:uac@172.16.2.1:5060>\r
Call-ID: 1-16003@11.0.0.3\r
CSeq: 1 INVITE\r
Contact: sip:sipp@11.0.0.3:59825\r
Max-Forwards: 70\r
Subject: Performance Test\r
Content-Type: application/sdp\r
Content-Length: 0\r
Refer-To: <sip:refertarget@11.0.0.3>\r
Referred-By: <sip:referrer@11.0.0.3:59825>\r
Record-Route: <sip:11.0.0.3;lr>\r
Route: <sip:11.0.0.3;lr>\r
\r
"""

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
s.send(MESSAGE.encode())
data = s.recv(BUFFER_SIZE)
s.close()