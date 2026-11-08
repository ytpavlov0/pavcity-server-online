"""Bounded HTTP workers created before accepting requests, then reused.

Thread.start waits for Python's bootstrap event. If a newly created thread
fails during bootstrap under memory pressure, that wait can strand the HTTP
accept loop. No request in this server starts another OS thread.
"""
from http.server import HTTPServer
from queue import Queue, Full
from threading import Thread


class StableWorkerHTTPServer(HTTPServer):
    request_queue_size = 128
    allow_reuse_address = True

    def __init__(self, *args, max_workers=64, pending_requests=128, **kwargs):
        self._jobs = Queue(maxsize=pending_requests)
        self._closing = False
        self._workers = []
        super().__init__(*args, **kwargs)
        for index in range(max_workers):
            worker = Thread(target=self._worker, name=f'pn-http-{index}', daemon=True)
            worker.start()
            self._workers.append(worker)

    def process_request(self, request, client_address):
        try:
            if self._closing:
                self.shutdown_request(request)
                return
            self._jobs.put_nowait((request, client_address))
        except Full:
            try:
                request.settimeout(1)
                request.sendall(b'HTTP/1.1 503 Service Unavailable\r\nConnection: close\r\nRetry-After: 1\r\nContent-Length: 0\r\n\r\n')
            except OSError:
                pass
            finally:
                self.shutdown_request(request)

    def _worker(self):
        while True:
            job = self._jobs.get()
            if job is None:
                self._jobs.task_done()
                return
            request, address = job
            try:
                request.settimeout(30)
                self.finish_request(request, address)
            except MemoryError:
                # Close this request and keep the existing worker reusable.
                # Formatting a traceback here can require more scarce memory.
                pass
            except Exception:
                self.handle_error(request, address)
            finally:
                try:
                    self.shutdown_request(request)
                finally:
                    self._jobs.task_done()

    def server_close(self):
        self._closing = True
        super().server_close()
        # Drain requests waiting for service; active handlers finish normally.
        while not self._jobs.empty():
            try:
                job = self._jobs.get_nowait()
            except Exception:
                break
            if job is not None:
                self.shutdown_request(job[0])
            self._jobs.task_done()
        for _ in self._workers:
            self._jobs.put_nowait(None)
