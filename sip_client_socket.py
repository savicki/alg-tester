#!/usr/bin/env python

import socket
import re
import argparse

REMOTE_IP = ''
TCP_PORT = 5060
BUFFER_SIZE = 1024
MESSAGE = """REGISTER sip:{{@local_ip}} SIP/2.0\r
CSeq: 4 REGISTER\r
Via: SIP/2.0/UDP {{@remote_ip}}:5060;branch=z9hG4bKde98b019-6e0f-ea11-829f-000c29f2ba09;rport\r
User-Agent: sipcmd/1.0.1\r
Authorization: Digest username="104", realm="asterisk", nonce="2ea44459", algorithm=MD5, response="769ce70baab0460cb24e841547ef6e0f"\r
From: <sip:104@{{@local_ip}}>;tag=6077af19-6e0f-ea11-829f-000c29f2ba09\r
Call-ID: b473af19-6e0f-ea11-829f-000c29f2ba09@hwServer\r
Organization: Command line VoIP testphone\r
To: <sip:104@{{@local_ip}}>\r
Contact: <sip:104@{{@remote_ip}}:5060>\r
Allow: INVITE,ACK,OPTIONS,BYE,CANCEL,SUBSCRIBE,NOTIFY,REFER,MESSAGE,INFO,PING,PRACK\r
Expires: 0\r
Content-Length: 0\r
Max-Forwards: 70\r
\r
"""

parser = argparse.ArgumentParser()
parser.add_argument("-dst_ip", help="destin IP", type=str, required=True)

args = parser.parse_args()


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print('Connecting to %s:%s ...' % (args.dst_ip, TCP_PORT))

s.connect((args.dst_ip, TCP_PORT))

REMOTE_IP = args.dst_ip
LOCAL_IP = s.getsockname()[0]

print('Connected. Local IP: %s' % LOCAL_IP)

MESSAGE = re.sub("{{@local_ip}}", LOCAL_IP, MESSAGE)
MESSAGE = re.sub("{{@remote_ip}}", REMOTE_IP, MESSAGE)

s.send(MESSAGE.encode())
data = s.recv(BUFFER_SIZE)
s.close()
