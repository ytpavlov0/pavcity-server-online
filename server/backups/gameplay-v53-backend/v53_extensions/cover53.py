"""Small mmap BVH of original static YBN blockers; never proves clear LOS.

Missing dynamic doors/props and unaudited district boundaries mean an empty ray
must remain UNVERIFIED. No client meshes/hit hints can override this decision.
"""
from pathlib import Path
import hashlib
import json
import math
import mmap
import struct

NODE = struct.Struct('<6f4I')
TRI = struct.Struct('<9fI')
HEADER = struct.Struct('<4sIII')


def ray_box(origin, direction, bounds, limit):
    low, high = 0., limit
    for i in range(3):
        if abs(direction[i]) < 1e-12:
            if origin[i] < bounds[i] or origin[i] > bounds[i+3]: return None
        else:
            a, b = (bounds[i]-origin[i])/direction[i], (bounds[i+3]-origin[i])/direction[i]
            low, high = max(low, min(a,b)), min(high, max(a,b))
            if low > high: return None
    return low


def ray_triangle(o, d, v, limit):
    e = (v[3]-v[0], v[4]-v[1], v[5]-v[2])
    f = (v[6]-v[0], v[7]-v[1], v[8]-v[2])
    h = (d[1]*f[2]-d[2]*f[1], d[2]*f[0]-d[0]*f[2], d[0]*f[1]-d[1]*f[0])
    determinant = sum(e[i]*h[i] for i in range(3))
    if abs(determinant) < 1e-10: return None
    inv = 1/determinant
    s = tuple(o[i]-v[i] for i in range(3))
    u = inv*sum(s[i]*h[i] for i in range(3))
    if u < -1e-7 or u > 1+1e-7: return None
    q = (s[1]*e[2]-s[2]*e[1], s[2]*e[0]-s[0]*e[2], s[0]*e[1]-s[1]*e[0])
    b = inv*sum(d[i]*q[i] for i in range(3))
    if b < -1e-7 or u+b > 1+1e-7: return None
    distance = inv*sum(f[i]*q[i] for i in range(3))
    return distance if .0001 <= distance <= limit else None


class Cover53:
    label = 'static-ybn-blockers-only'

    def __init__(self, directory):
        self.file = self.data = None
        self.directory = Path(directory)
        manifest = json.loads((self.directory/'manifest.json').read_text())
        # This release expressly cannot enable positive damage from partial data.
        if manifest.get('positive_coverage_verified') is not False:
            raise ValueError('Partial collision bank may not assert positive coverage')
        path = self.directory/'blockers53.bin'
        if not 16 <= path.stat().st_size <= 8*1048576: raise ValueError('Collision bank size')
        if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['sha256']: raise ValueError('Collision bank hash')
        self.file = path.open('rb')
        self.data = mmap.mmap(self.file.fileno(), 0, access=mmap.ACCESS_READ)
        magic, self.nodes, self.triangles, self.tri_offset = HEADER.unpack_from(self.data)
        if (magic != b'C53B' or not 1 <= self.nodes <= 100000 or self.triangles > 150000
            or self.tri_offset != HEADER.size+self.nodes*NODE.size
            or len(self.data) != self.tri_offset+self.triangles*TRI.size):
            self.close(); raise ValueError('Collision bank header')

    def trace(self, origin, direction, maximum, api=None, actor=None):
        if not self.data: return dict(outcome='unverified', distance=None)
        stack, visited, nearest = [0], 0, maximum
        blocked = False
        while stack and visited < 8192:
            index = stack.pop(); visited += 1
            if index >= self.nodes: return dict(outcome='unverified', distance=None)
            row = NODE.unpack_from(self.data, HEADER.size+index*NODE.size)
            if ray_box(origin, direction, row[:6], nearest) is None: continue
            left, right, start, count = row[6:]
            if count:
                if count > 8 or start+count > self.triangles: return dict(outcome='unverified', distance=None)
                for i in range(start, start+count):
                    triangle = TRI.unpack_from(self.data, self.tri_offset+i*TRI.size)
                    distance = ray_triangle(origin, direction, triangle, nearest)
                    if distance is not None: nearest, blocked = distance, True
            else: stack.extend((left, right))
        if blocked: return dict(outcome='blocked', distance=nearest)
        return dict(outcome='unverified', distance=None)

    def close(self):
        if self.data is not None: self.data.close(); self.data=None
        if self.file is not None: self.file.close(); self.file=None
