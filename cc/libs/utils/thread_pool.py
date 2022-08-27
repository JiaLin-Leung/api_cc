# coding: utf-8
# import time
import threading
# import queue
import logging
# POOL_SIZE = 50
# q = queue.Queue()
#
#
# def loop(id):
#     while 1:
#         f, args, kwargs = q.get()
#         try:
#             f(*args, **kwargs)
#         except Exception as e:
#             logging.error(e)
#
#
# def call(f, *args, **kwargs):
#     q.put((f, args, kwargs))
#
#
# def init():
#     for i in range(POOL_SIZE):
#         t = threading.Thread(target=loop, args=(i, ))
#         t.start()
#
# init()


class Mythiread(threading.Thread):
    def __init__(self, func, *args):
        threading.Thread.__init__(self)
        self.func = func
        self.args = args

    def getResult(self):
        return self.res

    def run(self):
        # self.res = apply(self.func, self.args)
        self.res = self.func(*self.args)


def call(f, *args, **kwargs):
    try:
        t = Mythiread(f, *args, **kwargs)
        t.start()
    except Exception as e:
        logging.error(e)
