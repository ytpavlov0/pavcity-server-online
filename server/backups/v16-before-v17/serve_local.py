"""Local mirror server with PAVCITY Online Database & Multiplayer API."""
import argparse
import gzip
import io
import json
import mimetypes
import os
import re
import sys
import webbrowser
from http.cookies import SimpleCookie
import socket
import threading
import session_api
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

class BoundedThreadingHTTPServer(ThreadingHTTPServer):
    """Bound RAM used by simultaneous asset/API requests during mass joins."""
    daemon_threads=True
    request_queue_size=128

    def __init__(self,*args,max_workers=64,**kwargs):
        self._request_slots=threading.BoundedSemaphore(max_workers)
        super().__init__(*args,**kwargs)

    def process_request(self,request,client_address):
        self._request_slots.acquire()
        try:super().process_request(request,client_address)
        except BaseException:
            self._request_slots.release()
            raise

    def process_request_thread(self,request,client_address):
        try:super().process_request_thread(request,client_address)
        finally:self._request_slots.release()

# Import multiplayer engine
try:
    import online_engine
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import online_engine

ROOT = Path(__file__).resolve().parent / 'mirror' / 'playgta5.com'
SUPPORT = Path(__file__).resolve().parent / 'support'
ENGINE_LOG = Path(__file__).resolve().parent / 'engine-debug.log'
ENGINE_LOG_LOCK = threading.Lock()
if not (ROOT / 'index.html').is_file():
    nested_root = ROOT.parent / 'mirror' / 'playgta5.com'
    if (nested_root / 'index.html').is_file():
        ROOT = nested_root

mimetypes.add_type('application/wasm', '.wasm')
mimetypes.add_type('text/javascript', '.js')

class Handler(SimpleHTTPRequestHandler):
    timeout=30
    def setup(self):
        super().setup()
        self.connection.settimeout(300)

    def __init__(self, *args, **kwargs):
        self.byte_range = None
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, TimeoutError):
            pass
        except Exception:
            pass

    def end_headers(self):
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.send_header('Cross-Origin-Resource-Policy', 'same-origin')
        self.send_header('Accept-Ranges', 'bytes')
        path_str = getattr(self, 'path', '/') or '/'
        req_path = urlsplit(path_str).path
        if req_path in ('/', '/index.html') or req_path.endswith(('.js', '.css')):
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
        elif req_path.endswith(('.wasm', '.rpf', '.wgsl', '.fxc', '.awc', '.ytd', '.yft', '.ydd')):
            self.send_header('Cache-Control', 'public, max-age=31536000, immutable')
        super().end_headers()

    def send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path == '/api/status':
            with session_api.LOCK:active_count=len(session_api.multiplayer.active(session_api.GTA_STATE))
            self.send_json({'success': True, 'native_bridge': 'v16', 'gta_multiplayer': True,'active_players':active_count,
                            'verification': 'V16: mobile memory/real constructor-worker tests, in-place health/seat, voice buffering and bounded server tests passed. Real ios32 WASM under desktop headless reached native avatar/frame samples. Actual iPhone crash cessation, GPU terrain, long-session and multi-device render remain unverified.',
                            'max_peers':32,'chat_radii':session_api.multiplayer.CHAT_RADIUS,'voice_radius':30})
            return
        if url.path == '/api/chat/list':
            msgs = online_engine.get_recent_chat(30)
            self.send_json({'success': True, 'messages': msgs})
            return
        elif url.path == '/api/players':
            players = online_engine.get_active_players()
            self.send_json({'success': True, 'players': players})
            return
        super().do_GET()

    def send_head(self):
        self.byte_range = None
        url = urlsplit(self.path)
        support_files = {'/__support/': 'index.html', '/__support/check.js': 'check.js'}
        if self.server.server_address[1]==8002:
            support_files['/__support/gameplay.html']='gameplay-preview.html'
            support_files['/__support/gameplay-v5.html']='gameplay-v5-preview.html'
            support_files['/__support/gameplay-v6.html']='gameplay-v6-preview.html'
            support_files['/__support/gameplay-v7.html']='gameplay-v7-preview.html'
            support_files['/__support/gameplay-v8.html']='gameplay-v8-preview.html'
            support_files['/__support/gameplay-v10.html']='gameplay-v10-preview.html'
            support_files['/__support/gameplay-v11.html']='gameplay-v11-preview.html'
            support_files['/__support/gameplay-v12.html']='gameplay-v12-preview.html'
            support_files['/__support/gameplay-v15.html']='gameplay-v15-preview.html'
            support_files['/__support/native-v16.html']='native-v16-preview.html'
            support_files['/__support/mobile-startup-v13.html']='mobile-startup-v13.html'
            support_files['/__support/mobile-startup-v14.html']='mobile-startup-v14.html'
        if self.server.server_address[1]==8001:
            support_files['/__support/native-v4.html']='native-v4-preview.html'
            support_files['/__support/native-v4-guard.js']='dev-tools/native_v4_guard.js'
            support_files['/__support/native-v5.html']='native-v5-preview.html'
            support_files['/__support/native-v5-guard.js']='dev-tools/native_v5_guard.js'
        support_name = support_files.get(url.path)
        if support_name:
            path = SUPPORT / support_name
            if not path.is_file():
                self.send_error(404)
                return None
            self.send_response(200)
            self.send_header('Content-Type', self.guess_type(str(path)))
            self.send_header('Content-Length', str(path.stat().st_size))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            return path.open('rb')

        if not self.headers.get('Range'):
            # Precompressed versioned WASM: streaming compilation sees decoded
            # bytes, ranges still refer to the original uncompressed resource.
            accept=self.headers.get('Accept-Encoding','')
            encodings={}
            for item in accept.split(','):
                bits=item.strip().split(';');quality=1.0
                for flag in bits[1:]:
                    if flag.strip().startswith('q='):
                        try:quality=float(flag.strip()[2:])
                        except ValueError:quality=0
                encodings[bits[0].lower()]=quality
            if re.fullmatch(r'/b/[a-f0-9]+/game-pn-(?:online|mobile32|ios32)-v(?:11|12|13|14|15|16)\.wasm',url.path) and encodings.get('gzip',encodings.get('*',0))>0:
                original=Path(self.translate_path(url.path));packed=original.with_suffix('.wasm.gz')
                if original.is_file() and packed.is_file():
                    self.send_response(200)
                    self.send_header('Content-Type','application/wasm')
                    self.send_header('Content-Encoding','gzip')
                    self.send_header('Vary','Accept-Encoding')
                    self.send_header('Content-Length',str(packed.stat().st_size))
                    self.send_header('X-Uncompressed-Length',str(original.stat().st_size))
                    self.end_headers()
                    return packed.open('rb')
            return super().send_head()

        path = Path(self.translate_path(self.path))
        if not path.is_file():
            self.send_error(404)
            return None
        size = path.stat().st_size
        match = re.fullmatch(r'bytes=(\d*)-(\d*)', self.headers['Range'])
        if not match or not any(match.groups()):
            self.send_error(416)
            return None
        start = int(match[1]) if match[1] else max(0, size - int(match[2]))
        end = min(size - 1, int(match[2])) if match[1] and match[2] else size - 1
        if start >= size or end < start:
            self.send_response(416)
            self.send_header('Content-Range', 'bytes */%d' % size)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return None
        self.byte_range = (start, end)
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(str(path)))
        self.send_header('Content-Range', 'bytes %d-%d/%d' % (start, end, size))
        self.send_header('Content-Length', str(end - start + 1))
        self.end_headers()
        source = path.open('rb')
        source.seek(start)
        return source

    def copyfile(self, source, outputfile):
        if self.byte_range is None:
            while True:
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                outputfile.write(chunk)
            return
        remaining = self.byte_range[1] - self.byte_range[0] + 1
        while remaining:
            chunk = source.read(min(1024 * 1024, remaining))
            if not chunk:
                break
            outputfile.write(chunk)
            remaining -= len(chunk)

    def do_POST(self):
        url = urlsplit(self.path)
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            self.send_error(400, 'Invalid Content-Length')
            return

        # Opt-in engine diagnostics (?log=1), kept outside the public mirror.
        if url.path == '/log':
            if not 0 <= length <= 65536:
                self.send_error(413)
                return
            cookies = SimpleCookie(self.headers.get('Cookie', ''))
            token = cookies['gta_session'].value if 'gta_session' in cookies else ''
            result, _ = session_api.dispatch('/api/auth/me', {}, token)
            if not result['success']:
                self.send_error(401)
                return
            body = self.rfile.read(length).decode('utf-8', errors='replace')
            with ENGINE_LOG_LOCK:
                if ENGINE_LOG.exists() and ENGINE_LOG.stat().st_size > 8 * 1024 * 1024:
                    ENGINE_LOG.replace(ENGINE_LOG.with_suffix('.previous.log'))
                with ENGINE_LOG.open('a', encoding='utf-8') as output:
                    output.write(body + '\n')
            self.send_response(204)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return

        # 1. Multiplayer & Auth API Endpoints
        if url.path.startswith('/api/'):
            if not 0 <= length <= 16384:
                self.send_error(413)
                return
            raw_body = self.rfile.read(length)
            try:
                payload = json.loads(raw_body) if raw_body else {}
                if not isinstance(payload, dict):
                    raise ValueError('Geçersiz istek.')
                cookies = SimpleCookie(self.headers.get('Cookie', ''))
                token = cookies['gta_session'].value if 'gta_session' in cookies else ''
                result, new_token = session_api.dispatch(url.path, payload, token)
                if new_token is not None:
                    body = json.dumps(result, ensure_ascii=False).encode('utf-8')
                    self.send_response(200)
                    secure = '; Secure' if self.headers.get('X-Forwarded-Proto') == 'https' else ''
                    self.send_header('Set-Cookie', 'gta_session='+new_token+'; HttpOnly; SameSite=Lax; Path=/; Max-Age='+('86400' if new_token else '0')+secure)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.send_header('Content-Length', str(len(body)))
                    self.send_header('Cache-Control', 'no-store')
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self.send_json(result)
            except (ValueError, TypeError) as error:
                self.send_json({'success': False, 'error': str(error)}, 400)
            except Exception:
                self.send_json({'success': False, 'error': 'Sunucu isteği tamamlayamadı.'}, 500)
            return

        # 2. Engine Batch I/O for game data streaming
        if url.path != '/data/batch':
            self.send_error(404)
            return

        if not 0 <= length <= 1024 * 1024:
            self.send_error(413, 'Invalid batch size')
            return
        try:
            runs = json.loads(self.rfile.read(length))
            if not isinstance(runs, list) or len(runs) > 1000:
                raise ValueError('invalid batch')
            selected = []
            data_root = (ROOT / 'data').resolve()
            for name, start, end in runs:
                if not isinstance(name, str) or type(start) is not int or type(end) is not int:
                    raise ValueError('invalid file/range types')
                file = (data_root / name).resolve()
                if not file.is_relative_to(data_root) or start < 0 or end < start:
                    raise ValueError('invalid file/range')
                selected.append((file, start, max(0, min(end + 1, file.stat().st_size) - start)))
            total = sum(n for _, _, n in selected)
            if total > 64 * 1024 * 1024:
                raise ValueError('batch exceeds 64 MiB')
            output = io.BytesIO()
            for file, start, n in selected:
                with file.open('rb') as source:
                    source.seek(start)
                    output.write(source.read(n))
            body = output.getvalue()
            compressed = parse_qs(url.query).get('gz') == ['1']
            if compressed:
                body = gzip.compress(body, compresslevel=1)
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('X-Run-Lengths', ','.join(str(n) for _, _, n in selected))
            if compressed:
                self.send_header('Content-Encoding', 'gzip')
            self.end_headers()
            self.wfile.write(body)
        except (ValueError, TypeError, OSError) as exc:
            self.send_error(400, str(exc))

if __name__ == '__main__':
    args = argparse.ArgumentParser(description='PAVCITY Los Santos Web Server')
    args.add_argument('--host', default='0.0.0.0', help='listen host')
    args.add_argument('--port', type=int, default=8000)
    args.add_argument('--root', type=Path, help='existing game directory')
    args.add_argument('--open', action='store_true', help='open browser')
    options = args.parse_args()
    if options.root:
        ROOT = options.root.resolve()
    if not (ROOT / 'index.html').is_file():
        args.error('Game files are missing.')
    try:
        server = BoundedThreadingHTTPServer((options.host, options.port), Handler, bind_and_activate=False)
        server.request_queue_size = 256
        if os.name == 'nt':
            server.allow_reuse_address = False
            server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        server.server_bind()
        server.server_activate()
    except OSError as error:
        args.error(f'Cannot start on port {options.port}: {error}')

    # Bind first: a second launcher must not reset the running world's vehicles.
    import pn_world
    pn_world.recover_vehicles()
    print('=========================================================', flush=True)
    print('   PN - Los Santos Web Server                          ', flush=True)
    print('   [HESAP + KARAKTER + GTA MULTIPLAYER DENEMESI]        ', flush=True)
    print('=========================================================', flush=True)
    print('Sunucu Portu : %d' % server.server_port, flush=True)
    print('Yerel Link   : http://127.0.0.1:%d/' % server.server_port, flush=True)
    print('=========================================================', flush=True)
    import time
    while True:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            break
        except Exception:
            time.sleep(0.2)
    server.server_close()
