import socket
import threading
import sys
import Queue
import traceback
class NoResultPending(Exception):
    '''All works requests have been processed'''
    pass

class NoWorkersAvailable(Exception):
    '''No work threads availabe to process remaining requests'''

def handle_thread_exception(request, exc_info):
    traceback.print_exception(*exc_info)

class WorkThread(threading.Thread):
    def __init__(self, requestQueue, resultQueue, poll_timeout = 5, **kwargs):
        threading.Thread.__init__(self, **kwargs)
        self._requestQueue = requestQueue
        self._resultQueue = resultQueue
        self.setDaemon(True)
        self.poll_timeout = poll_timeout
        self._dismissed = threading.Event()
        self.start()

    def run(self):
        while True:
            if self._dismissed.is_set():
                self._requestQueue.put(request)
                break
            try:
                #print 'work thread start get request'
                request = self._requestQueue.get(True, self.poll_timeout)
                #print 'get request id %d and queue size %s' %(request.requestID, str(self._requestQueue.qsize()))
            except:
                continue
            else:
                if self._dismissed.is_set():
                    break
                try:
                    result = request.callable(*request.args, **request.kwargs)
                    #print 'request id %d has return' % request.requestID
                    self._resultQueue.put((request, result))
                except:
                    request.exception = True
                    self._resultQueue.put((request, sys.exc_info()))
    def dismiss(self):
        self._dismissed.set()


class WorkRequest:
    def __init__(self, callable, args = None, kwargs = None, requestID = None, callback = None, exc_callback = handle_thread_exception):
        if requestID == None:
            self.requestID = id(self)
        else:
            try:
                self.requestID = hash(requestID)
            except TypeError:
                raise TypeError('RequestID must be hashable')
        self.args = args or []
        self.kwargs = kwargs or {}
        self.callable = callable
        self.callback = callback
        self.exception = False
        self.exc_callback = exc_callback

class ThreadPool:
    def __init__(self, num_threads, req_size = 3, result_size = 3, poll_timeout = 5):
        self._requestQueue = Queue.Queue(req_size)
        self._resultQueue = Queue.Queue(result_size)
        self.workers = []
        self.dismissWorkers = []
        self.workRequest = {}
        self.createWorkers(num_threads, poll_timeout)

    def createWorkers(self, num_threads, poll_timeout):
        for x in range(num_threads):
            self.workers.append(WorkThread(self._requestQueue, self._resultQueue, poll_timeout))

    def dismissWorkers(self, number, do_join):
        dismiss_list = []
        for i in range(min(number, len(self.workers))):
            work = self.workers.pop()
            work.dismiss()
            dismiss_list.append(work)
        if do_join:
            for worker in dismiss_list:
                worker.join()
        else:
            self.dismissWorkers.extend(dismiss_list)

    def joinAlldismissWorkers(self):
        for worker in self.dismissWorkers:
            worker.join()
        dismissWorkers = []

    def putRequest(self, request, block = True, timeout = None):
        assert isinstance(request, WorkRequest)
        assert not getattr(request, 'exception', None)
        #print 'Queue size : ' + str(self._requestQueue.full())
        self._requestQueue.put(request, True, timeout)
        self.workRequest[request.requestID] = request

    def poll(self, block = False):
        while True:
            '''
            if not self.workRequest:
                raise NoResultPending
            elif block and not self.workers:
                raise NoWorkersAvailable
                '''
            try:
                #print 'start get result queue ############'
                request, result = self._resultQueue.get(block = True)
                #print 'get result queue size ' + str(self.resultQueue.qsize())
                if request.exception and request.exc_callback:
                    request.exc_callback(request, result)
                if request.callback and not (request.exception and request.exc_callback):
                    request.callback(request, result)
                #del self.workRequest[request.reuqestID]
            except:
                continue