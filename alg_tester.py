#!/bin/python

import glob
import argparse
import socket
import re
from time import sleep

TCP_PORT = 5060


RNRN = '\r\n\r\n'
# search \r\n\r\n
# search Content-Length
# locate end of msg
def do_parse_msgs(content):
     msgs = []
     st = 0

     while st < len(content):
          end = content.find(RNRN, st)
          if end > st:
               m = re.match(r"[\w\W]*?Content-Length:\W*(\d+)", content[st:end])

               if m != None:
                    content_len = int(m.group(1))
               else:
                    content_len = 0

               end = end + len(RNRN)  + content_len

               print '[%s, %s) content_len: %s' % (st, end, content_len)

               if end > len(content):
                    end = len(content)

               msg = content[st:end]
               msgs.append(msg)

               print '"%s"' % msg

               st = end
          else:
               break

     return msgs

def do_edit_msg(msg, replace_arr, update_cl):
     for r in replace_arr:
          print 'replace \'%s\' with \'%s\'' % (r[0], r[1])
          msg = msg.replace(r[0], r[1])

     if update_cl: # @msg contains single SIP message
          end = msg.find(RNRN)
          if end > 0:
               end = end + len(RNRN)
               content_len = len(msg) - end;

               def replace_content_len(m):
                    return m.group(1) + str(content_len)

               msg = re.sub(r"(Content-Length:\W*)(\d+)", replace_content_len, msg)

               print "=======\n'%s'=======" % msg

     return msg

def process_file(content, args):

     if args.parse_msg == False and len(args.r) == 0:
          return content

     if args.parse_msg:
          msgs = do_parse_msgs(content)
     else:
          msgs = [content];

     if len(args.r) > 0:
          for ind, msg in enumerate(msgs):
               msgs[ind] = do_edit_msg(msg, args.r, args.parse_msg)

     return ''.join(msgs)

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

parser = argparse.ArgumentParser()

parser.add_argument("-dst_ip", help="destin IP", type=str, required=True)
parser.add_argument("-dst_port", help="destin port", type=int, default=TCP_PORT)
parser.add_argument("-fskip", help="num of filenames to skip", type=int, default=0)
parser.add_argument("-fcount", help="limit of filenames", type=int, required=True)
parser.add_argument("-fmask", help="mask of filename", type=str, required=True)
parser.add_argument("-r", help="replace pattern, e.g. '-r search/replace search2/replace2'", type=str, nargs="+", default='')
parser.add_argument("-parse_msg", help="don't update 'Content-Length:' field", type=str2bool, default=True)
# iTODO: delay

args = parser.parse_args()


if args.fcount > 1:
     args.parse_msg = False

if args.r != '':
     for ind, repl in enumerate(args.r):
          m = re.match(r"([\w\W]+?)/([\w\W]+)", repl)
          if m != None:
               args.r[ind] = (m.group(1), m.group(2))
          else:
               print 'wrong replace argument \'%s\', it must match patter \'search_word/replace_word\'' % repl

# print "args.fmask: '%s'" % args.fmask
# print "-r:'%s'" % args.r
# print "-parse_msg: '%s'" % args.parse_msg


filenames = sorted([f for f in glob.glob("./" + args.fmask)]) 

f_index = 0
while f_index < args.fskip:
     filenames.pop(0)
     f_index = f_index + 1

if args.fskip:
     print "skipped first %s files" % args.fskip

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
s.connect((args.dst_ip, args.dst_port))

f_index = 0
f_limit = args.fcount

while f_index < f_limit:
     for filename in filenames:
          f = open(filename, mode='r') 
          f_content = f.read()

          orig_len = len(f_content)

          f_content = process_file(f_content, args)

          sent_bytes = s.send(f_content.encode('ascii'))

          # e.g. "[2] 'tomsk_7.txt' read 460, write 482, sent 482 bytes"
          print "[%s] '%s' read %s, write %s, sent %s bytes" % (f_index, filename, orig_len, len(f_content), sent_bytes)
          
          f_index = f_index + 1

          if f_index == f_limit:
               print "File limit %d reached, stop" % f_limit
               break

# sleep(0.5)
s.recv(10000)
s.close()
