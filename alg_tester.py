#!/bin/python

import glob
import argparse
import socket
import re
import sys
import io
from time import sleep

# iTODO: highlight IPs in output

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKRED = '\033[31m'
    OKGREEN = '\033[32m'
    OKYELLOW = '\033[33m'
    OKMAGENTA = '\033[35m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


TCP_PORT = 5060


RNRN = '\r\n\r\n'


# search \r\n\r\n
# search Content-Length
# locate end of msg
# return array of SIP messages
def do_parse_msgs(content, args):
    msgs = []
    st = 0

    ind = 0
    while st < len(content):
        end = content.find(RNRN, st)
        if end > st:
            m = re.match(r"[\w\W]*?Content-Length:\W*(\d+)", content[st:end])

            if m is not None:
                content_len = int(m.group(1))
            else:
                content_len = 0

            end = end + len(RNRN) + content_len
            ind = ind + 1

            print '[do_parse_msgs] %d-th original msg at [%s, %s) of %d bytes with Content-Length: %s' % (ind, st, end, end - st, content_len)

            if end > len(content):
                end = len(content)

            msg = content[st:end]
            msgs.append(msg)

            if args.fdump:
                print(('[do_parse_msgs] ' + bcolors.OKMAGENTA + '\'%s\'' + bcolors.ENDC) % msg)

            st = end
        else:
            break

    return msgs


def do_edit_msg(msg, replace_arr, update_cl):
    orig_len = len(msg)

    for r in replace_arr:
        print((bcolors.OKRED + 'replace \'%s\' with \'%s\'' + bcolors.ENDC) % (r[0], r[1]))
        msg = msg.replace(r[0], r[1])

    if update_cl:  # @msg is single SIP message
        end = msg.find(RNRN)
        if end > 0:
            end = end + len(RNRN)
            content_len = len(msg) - end

            def replace_content_len(m):
                return m.group(1) + str(content_len)

            msg = re.sub(r"(Content-Length:\W*)(\d+)", replace_content_len, msg)

            print('Updated msg of %d => %d bytes with Content-Length: %s' % (orig_len, len(msg), content_len))
            print((bcolors.OKMAGENTA + '\'%s\'' + bcolors.ENDC) % msg)

    return msg, len(msg)


def do_update_content_length(submsg_arr):
    msg = ""
    for submsg in submsg_arr:
        msg = msg + submsg

    # where Content-Length: found and fixed
    submsg_ind = -1

    end = msg.find(RNRN)
    if end > 0:
        end = end + len(RNRN)
        content_len = len(msg) - end

        def replace_content_len(m):
            print("new Content-Length: %d" % content_len)
            return m.group(1) + str(content_len)

        for ind, submsg in enumerate(submsg_arr):
            if re.search(r"(Content-Length:\W*)(\d+)", submsg):
                submsg_ind = ind
                submsg_arr[ind] = re.sub(r"(Content-Length:\W*)(\d+)", replace_content_len, submsg)

    # msg_size = 0
    # for submsg in submsg_arr:
    #      msg_size = msg_size + len(submsg)

    return submsg_arr, submsg_ind


# parse message(s), then
# edit each of message(s)
def process_file(content, args, f_chunk_lens):
    if args.parse_msg:
        msgs = do_parse_msgs(content, args)
    else:
        print((bcolors.OKMAGENTA + '\'%s\'' + bcolors.ENDC) % content)
        msgs = [content]

    print("found and parsed %s complete SIP messages" % len(msgs))

    #   MSG |-----------|-----------|
    #
    # chunk |-----------------------|
    # chunk |-------|---------------|
    # chunk |--------------|--------|
    #
    # chunk |----|------|-----------|
    #
    # chunk |-------|------|--------|
    # submsg|-------*---*--*--------|
    #
    # chunk |---|---|--------|------|

    sub_msgs = []
    sub_msgs_info = []
    chunk_ind = 0
    chunk_off = 0
    # offset within message
    st_off = 0
    for msg_ind, msg in enumerate(msgs):
        msg_len = len(msg)
        msg_len_copy = msg_len

        # print("** msg_len: %d, st_off: %d, chunk_off: %d" % (msg_len_copy, st_off, chunk_off))

        while msg_len > 0 and chunk_ind < len(f_chunk_lens):
            chunk_len = f_chunk_lens[chunk_ind] - chunk_off
            # print("chunk_len: %s, msg_len: %d, chunk_off: %d" % (chunk_len, msg_len, chunk_off))
            if chunk_len >= msg_len:
                end_off = msg_len

                if chunk_len > msg_len:
                    chunk_off = chunk_off + msg_len
                else:
                    chunk_off = 0
                msg_len = 0
            else:
                end_off = chunk_len
                msg_len = msg_len - chunk_len
                chunk_off = 0

            submsg = msg[st_off:st_off + end_off]
            sub_msgs.append(submsg)
            sub_msgs_info.append((msg_ind, chunk_ind))

            if chunk_off == 0:
                chunk_ind = chunk_ind + 1

            st_off += end_off
            # print("st_off: %s, chunk_off: %d" % (st_off, chunk_off))

        # skip off processed message
        st_off -= msg_len_copy

    # print(sub_msgs_info)

    for ind, submsg in enumerate(sub_msgs):
        submsg_len = len(submsg)
        if len(args.r) > 0:
            sub_msgs[ind], submsg_newlen = do_edit_msg(submsg, args.r, False)

        info = sub_msgs_info[ind]
        print("submsg [%d] of %d => %d bytes is part of msg [%d], file chunk [%d]" % (ind, submsg_len, submsg_newlen, info[0], info[1]))

    # append fake (zero-len) *next* msg beyond of last
    sub_msgs.append('')
    sub_msgs_info.append((sub_msgs_info[-1][0] + 1, sub_msgs_info[-1][1] + 1))

    # Locate submessages which forms another message, 
    # and update "Content-Length:" header in submessage where this header located
    cur_msg_ind = -1
    st_ind = 0
    for ind, submsg in enumerate(sub_msgs):
        msg_ind = sub_msgs_info[ind][0]
        if msg_ind > cur_msg_ind:
            print("msg_ind: [%d] at [%d, %d) sub_msgs arr" % (cur_msg_ind, st_ind, ind))
            sub_msgs_arr, submsg_ind = do_update_content_length(sub_msgs[st_ind:ind])
            if submsg_ind >= 0:
                sub_msgs[st_ind + submsg_ind] = sub_msgs_arr[submsg_ind]

            cur_msg_ind = msg_ind
            st_ind = ind

    chunks = []
    chunk_content = ""
    cur_msg_chunk = -1
    for ind, submsg in enumerate(sub_msgs):
        msg_chunk = sub_msgs_info[ind][1]
        if msg_chunk > cur_msg_chunk:
            # if cur_msg_chunk >= 0:
            #      if args.fdump:
            #          print(("chunk [%d] of %d bytes:\n'" + bcolors.OKMAGENTA + "%s" + bcolors.ENDC + "'") % (cur_msg_chunk, len(chunk_content), chunk_content))
            #      else:
            #          print(("chunk [%d] of %d bytes") % (cur_msg_chunk, len(chunk_content)))

            if cur_msg_chunk >= 0:
                chunks.append(chunk_content)
            cur_msg_chunk = msg_chunk
            chunk_content = ""

        chunk_content = chunk_content + submsg

    return chunks


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
parser.add_argument("-fcount", help="limit of filenames", type=int, required=False, default=0)
parser.add_argument("-delay", help="delay in seconds between files, float value", type=float, required=True)
parser.add_argument("-recv_delay", help="delay in seconds before next socket receive, float value", type=float, required=False, default=0.5)
parser.add_argument("-fmask", help="mask of filename", type=str, required=True)
parser.add_argument("-fdump", help="dump each file during processing", type=str2bool, default=False)
parser.add_argument("-r", help="replace pattern, e.g. '-r search/replace search2/replace2'", type=str, nargs="+", default='')
# 'False':
# If input file provied with bogus/malfored 'Content-Length:', don't fix it.
# Nor ever validate message by message
# 'True' by default
parser.add_argument("-parse_msg", help="validate and update if needed 'Content-Length:' field", type=str2bool, default=True)

parser.add_argument("-mss", help="mss of segment", type=int, default=0)

args = parser.parse_args()

# no replace? just replay file(s)
if len(args.r) == 0:
    args.parse_msg = False

if args.r != '':
    for ind, arg in enumerate(args.r):
        m = re.match(r"([\w\W]+?)/([\w\W]+)", arg)
        if m is not None:
            args.r[ind] = (m.group(1), m.group(2))
        else:
            print 'wrong replace argument \'%s\', it must match patter \'search_word/replace_word\'' % arg

# print "args.fmask: '%s'" % args.fmask
# print "-r:'%s'" % args.r
# print "-parse_msg: '%s'" % args.parse_msg


# 'Internal_call__dir0__62067/VipNet_Internal_call__dir0__62067.pcap__1.txt'
def pcap2txtmsg_filename(key):
    # this regex for pcap2txtmsg.py output filenames
    m = re.match('(?:[\w\W]+?)__(\d+).txt', key)
    if m:
        return int(m.group(1))
    return key

filenames = sorted([f for f in glob.glob(args.fmask)], key=pcap2txtmsg_filename)

f_limit = 2**31 if args.fcount == 0 else args.fcount

if len(filenames) == 0:
    sys.exit('error: no matched files')

filenames = filenames[args.fskip:args.fskip + f_limit]

if len(filenames) == 0:
    sys.exit('error: no matched files after range applied')


if args.fskip:
    print "skipped first %s files" % args.fskip

print((bcolors.OKYELLOW + "Parse messages: %s" + bcolors.ENDC) % (args.parse_msg))

f_limit = 2**31 if args.fcount == 0 else args.fcount

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
print('Connecting to %s:%s ...' % (args.dst_ip, args.dst_port))
s.connect((args.dst_ip, args.dst_port))
print((bcolors.OKRED + 'Local %s:%s connected to %s:%s' + bcolors.ENDC) % (s.getsockname()[0], s.getsockname()[1], args.dst_ip, args.dst_port))


chunks = []
f_chunk_lens = []
f_index = 0

if not args.parse_msg:
    for filename in filenames:
        f = open(filename, mode='r')
        f_content = f.read()
        f.close()

        f_chunk_lens.append(len(f_content))

        print((bcolors.OKGREEN + "[%s] processing '%s' file of %d bytes.." + bcolors.ENDC) % (f_index, filename, len(f_content)))

        if len(args.r) > 0:
            f_content, chunk_newlen = do_edit_msg(f_content, args.r, False)

        chunks.append(f_content)
        f_index = f_index + 1
else:
    f_all_content = ""

    f_index = 0

    for filename in filenames:
        f = open(filename, mode='r')
        f_content = f.read()
        f.close()

        print((bcolors.OKGREEN + "[%s] reading '%s' file of %d bytes.." + bcolors.ENDC) % (f_index, filename, len(f_content)))

        f_all_content = f_all_content + f_content
        f_chunk_lens.append(len(f_content))
        f_index = f_index + 1

    chunks = process_file(f_all_content, args, f_chunk_lens)

total_sent_bytes = 0
total_recv_bytes = 0

for ind, chunk in enumerate(chunks):
    sent_bytes = s.send(chunk.encode('ascii'))
    total_sent_bytes = total_sent_bytes + sent_bytes
    recv_bytes = 0
    recv_buffers =[]
    try:
        while True:
            s.settimeout(args.recv_delay)
            recv_buffer = s.recv(4096)

            recv_bytes = len(recv_buffer)

            if recv_bytes > 0:
                recv_buffers.append(recv_buffer)

            total_recv_bytes = total_recv_bytes + recv_bytes

    except socket.timeout:
        pass

    if args.delay:
        sleep(args.delay)

    # e.g. "[2] 'tomsk_7.txt' read 460, write 482, sent 482 bytes"
    print((bcolors.OKYELLOW + "[%s] read: %s, after replace: %s, sent: %s, recv: %s bytes" + bcolors.ENDC) % (ind, f_chunk_lens[ind], len(chunk), sent_bytes, recv_bytes))

    if args.fdump:
        print(("'" + bcolors.OKMAGENTA + "%s" + bcolors.ENDC + "'") % (chunk))
        if recv_bytes > 0:
            for recv_buffer in recv_buffers:
                print(("'" + bcolors.OKRED + "%s" + bcolors.ENDC + "'") % (recv_buffer))

print "File limit %d reached, stop. Total sent bytes: %s, total recv bytes: %s" % (len(filenames), total_sent_bytes, total_recv_bytes)

sleep(3600)
s.close()
