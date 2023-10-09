import time
import threading


start_time = time.time()


def action():
    print('action ! -> time : {:.1f}s'.format(time.time()-start_time))


class SetInterval:
    def __init__(self, interval, action):
        self.interval = interval
        self.action = action
        self.stopEvent = threading.Event()
        thread = threading.Thread(target=self.__setInterval)
        thread.start()


    def __setInterval(self):
        nextTime = time.time() + self.interval

        while not self.stopEvent.wait(nextTime-time.time()):
            self.action()


    def cancel(self):
        self.stopEvent.set()


# 
# intval = SetInterval(0.6, action)
# print('just after setInterval -> time : {:.1f}s'.format(time.time()-start_time))

# # will stop interval in 5s
# t=threading.Timer(3,intval.cancel)
# t.start()