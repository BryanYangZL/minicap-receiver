# coding: utf8
import socket, sys
import time
import os

class Minicap(object):
    BUFFER_SIZE = 4096
    JPG_SIZE = 10 * 1024 * 1024

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.jpg = bytearray(self.JPG_SIZE)
        self.jpg_cursor = 0
        self.timestamp = 0
        self.jpg_size = 0

    def connect(self):
        try:
            self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except Exception as e:
            print(e)
            sys.exit(1)
        self.__socket.connect((self.host, self.port))

    def on_image_transfered(self):
        if self.jpg[0] != 0xff and self.jpg[1] != 0xd8:
            print("not valid jpg format file ", self.timestamp)
            return

        file_name = os.path.join('imgs', str(time.time()) + '.jpg')
        with open(file_name, 'wb') as f:
            f.write(self.jpg[:self.jpg_size])

    def consume(self):

        readBannerBytes = 0
        bannerLength = 24
        readFrameBytes = 0
        frameBodyLength = 0

        while True:
            try:
                chunk = self.__socket.recv(self.BUFFER_SIZE)
            except Exception as e:
                print(e)
                sys.exit(1)

            cursor = 0
            buf_len = len(chunk)
            while cursor < buf_len:
                if readBannerBytes < bannerLength:   # recv banner at the first time after connect
                    cursor = bannerLength
                    readBannerBytes = bannerLength
                    if (chunk[0] != 1) and (chunk[1] != bannerLength):
                        print("recieve banner fail")
                        break
                elif readFrameBytes < 4:  # each frame have a header.include data length
                    frameBodyLength += (chunk[cursor] << (readFrameBytes * 8)) >> 0
                    cursor += 1
                    readFrameBytes += 1
                    self.jpg_size = frameBodyLength
                else: # recv jpg
                    if (frameBodyLength > self.JPG_SIZE):
                        print("jpg too large")
                        break

                    if buf_len - cursor >= frameBodyLength:
                        self.jpg[self.jpg_cursor: self.jpg_cursor + (frameBodyLength-cursor)] = chunk[cursor:cursor + frameBodyLength]
                        self.jpg_cursor += (frameBodyLength - cursor)

                        self.on_image_transfered()

                        cursor += frameBodyLength
                        frameBodyLength = readFrameBytes = 0
                        self.jpg_cursor = 0
                    else:
                        self.jpg[self.jpg_cursor:] = chunk[cursor:buf_len]
                        self.jpg_cursor += (buf_len - cursor)
                        frameBodyLength -= buf_len - cursor
                        readFrameBytes += buf_len - cursor
                        cursor = buf_len


if '__main__' == __name__:
    mc = Minicap('localhost', 1717)
    mc.connect()
    mc.consume()