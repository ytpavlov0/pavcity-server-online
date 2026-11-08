// PAVCITY realtime server (172) + server console.
// Build: C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /nologo /optimize /out:pavrt.exe pavrt.cs
// (C# 5 / .NET Framework 4.x, no external packages.)
//
// Players send their fast-changing state over a WebSocket (/rt?t=<ticket>) ~15 times a second:
//   "p,<x>,<y>,<z>,<heading>,<speed>,<vx>,<vy>,<vz>,<weapon>,<flags>,<aimx>,<aimy>,<aimz>,<vehicle>,<seat>,<dim>"
//   optionally followed by ";v,<vid>,<x>,<y>,<z>,<heading>,<rx>,<ry>,<rz>,<vx>,<vy>,<vz>,<body>" (driver's car).
// "q,<n>" is answered at once with {"q":<n>} (196: the client measures its realtime ping).
// Every 66 ms each client gets the nearest 40 other players (and the cars they drive) within 400 m:
//   {"t":<ms>,"p":[[cid,x,y,z,h,spd,vx,vy,vz,weapon,flags,ax,ay,az,veh,seat,ageMs],...],"v":[[vid,x,...,body,ageMs],...]}
// The Python game server stays the authority (health, appearance, seats, hits, money, chat); it issues the tickets
// (HMAC-SHA256 over "c=<char>&s=<server_id>&e=<unix exp>" with the shared secret backups/rt172.secret).
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.WebSockets;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

class Client {
    public int Cid; public int Sid; public WebSocket Ws; public string Ip;
    public double[] P = new double[16]; public long PAt;          // last player state + Stopwatch ms
    public double[] V = new double[12]; public long VAt; public int Vid;
    public string N; public long NAt; public long ClaimAt = -100000;      // 201: shared population report (raw, validated) and claim rate
    public long ChatAt = -100000; public int Sending; public long Msgs; public long Sent; public long Dropped; public long Connected;
    // 176 voice: route signed by the game server (radio channel, phone partner, dimension) + an ordered send queue
    public int Radio, Call, Dim; public long RouteExp; public long VoiceIn, VoiceOut;
    public readonly ConcurrentQueue<byte[]> Out = new ConcurrentQueue<byte[]>(); public int Pumping;
}

static class Rt {
    public static readonly ConcurrentDictionary<int, Client> Clients = new ConcurrentDictionary<int, Client>();
    public static readonly Stopwatch Clock = Stopwatch.StartNew();
    public static byte[] Secret;
    public static string Root;
    public static long MsgsIn, MsgsOut, Rejected, Ticks;
    public static volatile string Notice = null; public static long NoticeAt;
    public static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
    static readonly object LogLock = new object();

    public static void Log(string s) {
        string line = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss", Inv) + " " + s;
        lock (LogLock) { try { File.AppendAllText(Path.Combine(Root, "backups", "pavrt.log"), line + Environment.NewLine); } catch { } }
    }

    static string B64(byte[] b) { return Convert.ToBase64String(b).TrimEnd('=').Replace('+', '-').Replace('/', '_'); }
    static byte[] Unb64(string s) { s = s.Replace('-', '+').Replace('_', '/'); while (s.Length % 4 != 0) s += "="; return Convert.FromBase64String(s); }

    // returns cid or 0
    public static int Verify(string ticket, out int sid) {
        sid = 0;
        try {
            int dot = ticket.IndexOf('.'); if (dot <= 0) return 0;
            byte[] payload = Unb64(ticket.Substring(0, dot)); byte[] sig = Unb64(ticket.Substring(dot + 1));
            byte[] want; using (var h = new HMACSHA256(Secret)) want = h.ComputeHash(payload);
            if (sig.Length != want.Length) return 0;
            int diff = 0; for (int i = 0; i < sig.Length; i++) diff |= sig[i] ^ want[i];
            if (diff != 0) return 0;
            int cid = 0; long exp = 0;
            foreach (var part in Encoding.ASCII.GetString(payload).Split('&')) {
                var kv = part.Split('='); if (kv.Length != 2) continue;
                if (kv[0] == "c") cid = int.Parse(kv[1], Inv); else if (kv[0] == "s") sid = int.Parse(kv[1], Inv); else if (kv[0] == "e") exp = long.Parse(kv[1], Inv);
            }
            long now = (long)(DateTime.UtcNow - new DateTime(1970, 1, 1)).TotalSeconds;
            return (cid > 0 && exp > now) ? cid : 0;
        } catch { return 0; }
    }

    // ints = indices that are integer ids/hashes (weapon hash up to 2^32, flags); everything else is a finite coordinate
    static bool ParseInto(string[] parts, int start, double[] dst, int n, int[] ints) {
        if (parts.Length < start + n) return false;
        for (int i = 0; i < n; i++) {
            double v; if (!double.TryParse(parts[start + i], NumberStyles.Float, Inv, out v) || double.IsNaN(v) || double.IsInfinity(v)) return false;
            if (Array.IndexOf(ints, i) >= 0) { if (v < -2147483648.0 || v > 4294967295.0) return false; v = Math.Floor(v); }
            else if (Math.Abs(v) > 1e6) return false;
            dst[i] = v;
        }
        return true;
    }
    static readonly int[] PInts = { 8, 9, 13, 14, 15 };
    static readonly int[] VInts = { 0 };

    // ---- ordered sending: one WebSocket send at a time per client; state updates are dropped when the queue backs up,
    // audio is not (bounded at 64 frames)
    public static void Enqueue(Client c, byte[] bytes, bool audio) {
        if (c.Ws.State != WebSocketState.Open) return;
        if (!audio && c.Out.Count > 2) { c.Dropped++; return; }
        if (audio && c.Out.Count > 64) { c.Dropped++; return; }
        c.Out.Enqueue(bytes);
        if (Interlocked.CompareExchange(ref c.Pumping, 1, 0) == 0) Task.Run(() => Pump(c));
    }
    static async Task Pump(Client c) {
        while (true) {
            byte[] b;
            while (c.Out.TryDequeue(out b)) {
                try { await c.Ws.SendAsync(new ArraySegment<byte>(b), WebSocketMessageType.Text, true, CancellationToken.None); Interlocked.Increment(ref MsgsOut); c.Sent++; }
                catch { byte[] x; while (c.Out.TryDequeue(out x)) { } break; }
            }
            Interlocked.Exchange(ref c.Pumping, 0);
            if (c.Out.IsEmpty || Interlocked.CompareExchange(ref c.Pumping, 1, 0) != 0) return;
        }
    }

    // ---- voice route: "c=<char>&r=<radio faction or 0>&k=<phone partner char or 0>&d=<dimension>&e=<unix exp>" signed by
    // the game server with the shared secret; only the game server decides who hears whom beyond the 30 m proximity
    public static bool VerifyRoute(Client c, string token) {
        try {
            int dot = token.IndexOf('.'); if (dot <= 0) return false;
            byte[] payload = Unb64(token.Substring(0, dot)); byte[] sig = Unb64(token.Substring(dot + 1));
            byte[] want; using (var h = new HMACSHA256(Secret)) want = h.ComputeHash(payload);
            if (sig.Length != want.Length) return false;
            int diff = 0; for (int i = 0; i < sig.Length; i++) diff |= sig[i] ^ want[i];
            if (diff != 0) return false;
            int cid = 0, radio = 0, call = 0, dim = 0; long exp = 0;
            foreach (var part in Encoding.ASCII.GetString(payload).Split('&')) {
                var kv = part.Split('='); if (kv.Length != 2) continue;
                if (kv[0] == "c") cid = int.Parse(kv[1], Inv); else if (kv[0] == "r") radio = int.Parse(kv[1], Inv); else if (kv[0] == "k") call = int.Parse(kv[1], Inv);
                else if (kv[0] == "d") dim = int.Parse(kv[1], Inv); else if (kv[0] == "e") exp = long.Parse(kv[1], Inv);
            }
            long now = (long)(DateTime.UtcNow - new DateTime(1970, 1, 1)).TotalSeconds;
            if (cid != c.Cid || exp <= now) return false;
            c.Radio = radio; c.Call = call; c.Dim = dim; c.RouteExp = exp; return true;
        } catch { return false; }
    }
    static bool RouteOk(Client c) { return c.RouteExp > (long)(DateTime.UtcNow - new DateTime(1970, 1, 1)).TotalSeconds; }

    // same rules as the game server's audio()/radio61: phone partner at any distance (both sides agree), else proximity
    // (same dimension, 30 m), else the same faction radio when neither side is in a call. Modes: 0 nearby, 1 radio, 2 phone.
    public static int VoiceRadius = 30;
    public static void RelayVoice(Client s, long seq, string b64) {
        long now = Clock.ElapsedMilliseconds; s.VoiceIn++;
        if (!RouteOk(s) || s.PAt == 0 || now - s.PAt > 5000) return;
        string head = "{\"a\":[" + s.Cid.ToString(Inv) + "," + seq.ToString(Inv) + ",";
        var sp = s.P;
        foreach (var r in Clients.Values) {
            if (r == s || r.Ws.State != WebSocketState.Open) continue;
            int mode = -1; bool rok = RouteOk(r);
            if (rok && s.Call != 0 && s.Call == r.Cid && r.Call == s.Cid) mode = 2;
            else if (rok && r.Dim == s.Dim && r.PAt > 0 && now - r.PAt < 5000) {
                double dx = r.P[0] - sp[0], dy = r.P[1] - sp[1], dz = r.P[2] - sp[2];
                if (dx * dx + dy * dy + dz * dz <= VoiceRadius * VoiceRadius) mode = 0;
            }
            if (mode < 0 && rok && s.Call == 0 && r.Call == 0 && s.Radio != 0 && s.Radio == r.Radio) mode = 1;
            if (mode < 0) continue;
            var sb = new StringBuilder(head.Length + b64.Length + 64); sb.Append(head);
            F(sb, sp[0]); sb.Append(','); F(sb, sp[1]); sb.Append(','); F(sb, sp[2]); sb.Append(',').Append(mode).Append(",\"").Append(b64).Append("\"]}");
            Enqueue(r, Encoding.UTF8.GetBytes(sb.ToString()), true); s.VoiceOut++;
        }
    }

    public static void Handle(Client c, string msg) {
        Interlocked.Increment(ref MsgsIn); c.Msgs++;
        if (msg.Length > 12000) return;
        if (msg.StartsWith("a,")) {          // a,<seq>,<base64 pcm16 16 kHz>
            var ap = msg.Split(','); long seq;
            if (ap.Length == 3 && long.TryParse(ap[1], NumberStyles.Integer, Inv, out seq) && ap[2].Length >= 400 && ap[2].Length <= 11000) {
                foreach (char ch in ap[2]) if (!(char.IsLetterOrDigit(ch) || ch == '+' || ch == '/' || ch == '=')) return;
                RelayVoice(c, seq, ap[2]);
            }
            return;
        }
        if (msg.StartsWith("r,")) { VerifyRoute(c, msg.Substring(2)); return; }
        if (msg.StartsWith("q,")) {            // 196: ping echo, q,<n> -> {"q":<n>} to the sender only
            var n = msg.Substring(2); if (n.Length >= 1 && n.Length <= 12 && n.All(char.IsDigit)) Enqueue(c, Encoding.UTF8.GetBytes("{\"q\":" + n + "}"), true);
            return;
        }
        foreach (var block in msg.Split(';')) {
            var parts = block.Split(',');
            if (parts.Length == 0) continue;
            if (parts[0] == "p") {
                var tmp = new double[16];
                if (ParseInto(parts, 1, tmp, 16, PInts)) { c.P = tmp; c.PAt = Clock.ElapsedMilliseconds; }
            } else if (parts[0] == "c") {
                c.ChatAt = Clock.ElapsedMilliseconds;      // "new chat line": the sender and nearby clients fetch it at once
            } else if (parts[0] == "n") {          // 201: n,<seq>,<x>,<y>,<z>,<count>,<16 numbers per row>: a host's own traffic and pedestrians
                if (block.Length <= 7000 && NBlock.IsMatch(block)) { c.N = block.Substring(2); c.NAt = Clock.ElapsedMilliseconds; }
            } else if (parts[0] == "k") {          // 201: k,<host char id>,<host handle>: a follower took a copied car; the host removes its own
                int hc, hh; long kt = Clock.ElapsedMilliseconds;
                if (parts.Length == 3 && kt - c.ClaimAt >= 250 && int.TryParse(parts[1], NumberStyles.Integer, Inv, out hc) && int.TryParse(parts[2], NumberStyles.Integer, Inv, out hh) && hc > 0 && hh > 0) { c.ClaimAt = kt; Claim(c, hc, hh); }
            } else if (parts[0] == "v") {
                var tmp = new double[12];
                if (ParseInto(parts, 1, tmp, 12, VInts) && tmp[0] > 0) { c.V = tmp; c.Vid = (int)tmp[0]; c.VAt = Clock.ElapsedMilliseconds; }
            }
        }
    }

    static readonly System.Text.RegularExpressions.Regex NBlock = new System.Text.RegularExpressions.Regex(@"^n(,-?(0|[1-9][0-9]{0,9})(\.[0-9]{1,3})?){5,800}$", System.Text.RegularExpressions.RegexOptions.Compiled);
    static long LastBcast = -1;
    static void Claim(Client from, int hostCid, int handle) {
        foreach (var h in Clients.Values) {
            if (h.Cid != hostCid || h.PAt <= 0 || h == from) continue;
            double dx = h.P[0] - from.P[0], dy = h.P[1] - from.P[1];
            if (dx * dx + dy * dy <= 400.0 * 400.0) Enqueue(h, Encoding.UTF8.GetBytes("{\"y\":[" + handle.ToString(Inv) + "]}"), true);
            return;
        }
    }

    static void F(StringBuilder sb, double v) { sb.Append(Math.Round(v, 3).ToString("0.###", Inv)); }

    public static void Broadcast() {
        long now = Clock.ElapsedMilliseconds; Interlocked.Increment(ref Ticks);
        var all = Clients.Values.Where(x => x.PAt > 0 && now - x.PAt < 3000).ToArray();
        // each player's fragment is formatted once per tick and reused for every receiver
        var pf = new Dictionary<Client, string>(all.Length); var vf = new Dictionary<Client, string>();
        foreach (var o in all) {
            var sb = new StringBuilder(160); var p = o.P;
            sb.Append('[').Append(o.Cid);
            for (int i = 0; i < 15; i++) { sb.Append(','); F(sb, p[i]); }
            sb.Append(',').Append(now - o.PAt).Append(']');
            pf[o] = sb.ToString();
            if (o.Vid > 0 && now - o.VAt <= 1500) {
                var vb = new StringBuilder(140); vb.Append('[').Append(o.Vid);
                for (int i = 1; i < 12; i++) { vb.Append(','); F(vb, o.V[i]); }
                vb.Append(',').Append(now - o.VAt).Append(']'); vf[o] = vb.ToString();
            }
        }
        // 201: each host report goes out once, in the first tick after it arrived
        var nf = new Dictionary<Client, string>();
        foreach (var o in all) if (o.N != null && o.NAt > LastBcast && now - o.NAt < 1000) nf[o] = "[" + o.Cid.ToString(Inv) + "," + (now - o.NAt).ToString(Inv) + "," + o.N + "]";
        LastBcast = now;
        string notice = Notice; if (notice != null && now - NoticeAt > 3000) { Notice = null; notice = null; }
        string tail = notice != null ? ",\"n\":\"" + notice.Replace("\\", "\\\\").Replace("\"", "\\\"") + "\"}" : "}";
        var receivers = Clients.Values.ToArray();
        Parallel.ForEach(receivers, new ParallelOptions { MaxDegreeOfParallelism = Environment.ProcessorCount }, c => {
            if (c.Ws.State != WebSocketState.Open) return;
            if (c.Out.Count > 2) { c.Dropped++; return; }
            var me = c.P;
            var near = new List<KeyValuePair<double, Client>>();
            if (c.PAt > 0) {
                foreach (var o in all) {
                    if (o == c) continue;
                    double dx = o.P[0] - me[0], dy = o.P[1] - me[1], dz = o.P[2] - me[2];
                    double d2 = dx * dx + dy * dy + dz * dz;
                    if (d2 <= 400.0 * 400.0) near.Add(new KeyValuePair<double, Client>(d2, o));
                }
            }
            near.Sort((a, b) => a.Key.CompareTo(b.Key));
            bool knock = now - c.ChatAt < 300;
            if (!knock) foreach (var kv in near) if (now - kv.Value.ChatAt < 300) { knock = true; break; }
            if (near.Count > 40) near.RemoveRange(40, near.Count - 40);
            var sb = new StringBuilder(64 + near.Count * 170);
            sb.Append("{\"t\":").Append(now);
            if (knock) sb.Append(",\"k\":1");
            sb.Append(",\"p\":[");
            for (int k = 0; k < near.Count; k++) { if (k > 0) sb.Append(','); sb.Append(pf[near[k].Value]); }
            sb.Append("],\"v\":[");
            bool first = true; string frag;
            foreach (var kv in near) if (vf.TryGetValue(kv.Value, out frag)) { if (!first) sb.Append(','); sb.Append(frag); first = false; }
            sb.Append(']');
            if (nf.Count > 0) { bool nfirst = true; foreach (var kv in near) if (nf.TryGetValue(kv.Value, out frag)) { sb.Append(nfirst ? ",\"x\":[" : ",").Append(frag); nfirst = false; } if (!nfirst) sb.Append(']'); }
            sb.Append(tail);
            Enqueue(c, Encoding.UTF8.GetBytes(sb.ToString()), false);
        });
    }
    public static async Task Serve(HttpListenerContext ctx) {
        var req = ctx.Request;
        string path = req.Url.AbsolutePath;
        if (path == "/rt/status") {
            var body = Encoding.UTF8.GetBytes(StatusJson());
            ctx.Response.ContentType = "application/json"; ctx.Response.AddHeader("Cache-Control", "no-store");
            ctx.Response.OutputStream.Write(body, 0, body.Length); ctx.Response.Close(); return;
        }
        if (path.StartsWith("/rt/admin/")) {
            // local console only: never through the tunnel (Cloudflare adds Cf-Connecting-Ip)
            if (req.Headers["Cf-Connecting-Ip"] != null || !IPAddress.IsLoopback(req.RemoteEndPoint.Address)) { ctx.Response.StatusCode = 403; ctx.Response.Close(); return; }
            string outp = "";
            if (path == "/rt/admin/players") outp = PlayersText();
            else if (path == "/rt/admin/say") { string m = req.QueryString["m"] ?? ""; if (m.Length > 0) { Notice = m.Length > 200 ? m.Substring(0, 200) : m; NoticeAt = Clock.ElapsedMilliseconds; Log("console: say " + m); outp = "ok"; } }
            var ob = Encoding.UTF8.GetBytes(outp); ctx.Response.ContentType = "text/plain; charset=utf-8"; ctx.Response.OutputStream.Write(ob, 0, ob.Length); ctx.Response.Close(); return;
        }
        if (path != "/rt" && path != "/rt/") { ctx.Response.StatusCode = 404; ctx.Response.Close(); return; }
        if (!req.IsWebSocketRequest) { ctx.Response.StatusCode = 426; ctx.Response.Close(); return; }
        string origin = req.Headers["Origin"] ?? "";
        if (origin != "" && origin != "https://your-domain.example" && !origin.StartsWith("http://127.0.0.1") && !origin.StartsWith("http://localhost")) {
            Interlocked.Increment(ref Rejected); ctx.Response.StatusCode = 403; ctx.Response.Close(); return;
        }
        int sid; int cid = Verify(req.QueryString["t"] ?? "", out sid);
        if (cid == 0) { Interlocked.Increment(ref Rejected); ctx.Response.StatusCode = 401; ctx.Response.Close(); return; }
        HttpListenerWebSocketContext wsc;
        try { wsc = await ctx.AcceptWebSocketAsync(null, 8192, TimeSpan.FromSeconds(15)); } catch { return; }
        var c = new Client { Cid = cid, Sid = sid, Ws = wsc.WebSocket, Ip = req.Headers["Cf-Connecting-Ip"] ?? req.RemoteEndPoint.Address.ToString(), Connected = Clock.ElapsedMilliseconds };
        Client old;
        if (Clients.TryGetValue(cid, out old)) { try { old.Ws.Abort(); } catch { } }
        Clients[cid] = c;
        var buf = new byte[16384];
        try {
            while (c.Ws.State == WebSocketState.Open) {
                int len = 0; WebSocketReceiveResult r;
                do {
                    r = await c.Ws.ReceiveAsync(new ArraySegment<byte>(buf, len, buf.Length - len), CancellationToken.None);
                    len += r.Count;
                } while (!r.EndOfMessage && len < buf.Length);
                if (r.MessageType == WebSocketMessageType.Close) break;
                if (!r.EndOfMessage) break;            // oversized
                Handle(c, Encoding.UTF8.GetString(buf, 0, len));
            }
        } catch { }
        Client cur;
        if (Clients.TryGetValue(cid, out cur) && cur == c) Clients.TryRemove(cid, out cur);
        try { c.Ws.Abort(); } catch { }
    }

    public static string PlayersText() {
        long now = Clock.ElapsedMilliseconds; var sb = new StringBuilder();
        foreach (var c in Clients.Values.OrderBy(x => x.Sid))
            sb.AppendLine(string.Format(Inv, "  ID {0,-4} karakter {1,-6} konum ({2,7:0},{3,7:0},{4,5:0})  son veri {5,5} ms  mesaj {6}  gönderilen {7}  atlanan {8}",
                c.Sid, c.Cid, c.P[0], c.P[1], c.P[2], c.PAt > 0 ? (now - c.PAt).ToString(Inv) : "-", c.Msgs, c.Sent, c.Dropped));
        return sb.ToString();
    }
    public static string StatusJson() {
        long now = Clock.ElapsedMilliseconds;
        int live = Clients.Values.Count(x => now - x.PAt < 3000);
        return "{\"realtime\":\"pavrt172\",\"connected\":" + Clients.Count + ",\"live\":" + live + ",\"msgs_in\":" + MsgsIn + ",\"msgs_out\":" + MsgsOut + ",\"rejected\":" + Rejected + ",\"ticks\":" + Ticks + ",\"uptime_s\":" + (now / 1000) + "}";
    }
}

static class Program {
    static string Root;
    static int PyPlayers() {
        try {
            var wc = new WebClient(); wc.Encoding = Encoding.UTF8;
            string s = wc.DownloadString("http://127.0.0.1:8000/api/status");
            int i = s.IndexOf("\"active_players\":"); if (i < 0) return -1;
            i += 17; int j = i; while (j < s.Length && (char.IsDigit(s[j]) || s[j] == ' ')) j++;
            return int.Parse(s.Substring(i, j - i).Trim(), Rt.Inv);
        } catch { return -1; }
    }
    static string ReadAll(string p) { try { return File.ReadAllText(p); } catch { return ""; } }
    static int BackendPid() {
        string s = ReadAll(Path.Combine(Root, "backups", "detached-server.json"));
        int i = s.IndexOf("\"pid\":"); if (i < 0) return 0; i += 6; int j = i; while (j < s.Length && (char.IsDigit(s[j]) || s[j] == ' ')) j++;
        int pid; return int.TryParse(s.Substring(i, j - i).Trim(), out pid) ? pid : 0;
    }
    static string BackendStarter() {
        // newest run_detached_gameplay_vNNN.py
        var best = Directory.GetFiles(Path.Combine(Root, "support", "dev-tools"), "run_detached_gameplay_v*.py")
            .Select(f => new { f, n = int.Parse(Path.GetFileNameWithoutExtension(f).Substring("run_detached_gameplay_v".Length).TrimEnd('b'), Rt.Inv) })
            .OrderByDescending(x => x.n).FirstOrDefault();
        return best == null ? null : best.f;
    }
    static void StartDetached(string exe, string args) {
        // WMI Win32_Process.Create: the child is not tied to this console (closing the console keeps the game running).
        var ps = new ProcessStartInfo("powershell.exe", "-NoProfile -Command \"Invoke-CimMethod Win32_Process -MethodName Create -Arguments @{CommandLine='" + exe.Replace("'", "''") + " " + args.Replace("'", "''") + "';CurrentDirectory='" + Root.Replace("'", "''") + "'} | Out-Null\"");
        ps.UseShellExecute = false; ps.CreateNoWindow = true;
        Process.Start(ps).WaitForExit(30000);
    }
    static bool BackendUp() { return PyPlayers() >= 0; }
    static void EnsureBackend() {
        if (BackendUp()) { Console.WriteLine("  Oyun sunucusu (Python) çalışıyor."); return; }
        string starter = BackendStarter(); if (starter == null) { Console.WriteLine("  Oyun sunucusu başlatıcısı bulunamadı."); return; }
        Console.WriteLine("  Oyun sunucusu başlatılıyor: " + Path.GetFileName(starter));
        StartDetached("\"" + Path.Combine(Root, "runtime", "python.exe") + "\"", "-X utf8 \"" + starter + "\"");
        for (int i = 0; i < 60 && !BackendUp(); i++) Thread.Sleep(2000);
        Console.WriteLine(BackendUp() ? "  Oyun sunucusu hazır." : "  UYARI: oyun sunucusu 2 dakikada açılmadı (backups/detached-server.log).");
    }
    static bool TunnelUp() {
        return Process.GetProcessesByName("cloudflared").Length > 0;
    }
    static void EnsureTunnel() {
        if (TunnelUp()) { Console.WriteLine("  Cloudflare tüneli (your-domain.example) çalışıyor."); return; }
        string cfg = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".cloudflared", "config.yml");
        Console.WriteLine("  Cloudflare tüneli başlatılıyor.");
        StartDetached("\"" + Path.Combine(Root, "cloudflared.exe") + "\"", "tunnel --config \"" + cfg + "\" --no-autoupdate --logfile \"" + Path.Combine(Root, "backups", "tunnel-named.log") + "\" run pavcity");
    }
    static void RestartBackend() {
        int pid = BackendPid();
        string starter = BackendStarter(); if (starter == null) { Console.WriteLine("  Başlatıcı yok."); return; }
        Console.WriteLine("  Oyun sunucusu yeniden başlatılıyor (oyuncular birkaç saniye içinde yeniden bağlanır)...");
        try { if (pid > 0) Process.GetProcessById(pid).Kill(); } catch { }
        Thread.Sleep(2000);
        StartDetached("\"" + Path.Combine(Root, "runtime", "python.exe") + "\"", "-X utf8 \"" + starter + "\"");
        for (int i = 0; i < 60 && !BackendUp(); i++) Thread.Sleep(2000);
        Console.WriteLine(BackendUp() ? "  Oyun sunucusu tekrar hazır." : "  UYARI: oyun sunucusu açılmadı (backups/detached-server.log).");
        Rt.Log("console: restart backend");
    }
    static void Maint(string arg) {
        string p = Path.Combine(Root, "backups", "maintenance171.json");
        string s = ReadAll(p);
        if (s == "") { Console.WriteLine("  maintenance171.json yok."); return; }
        if (arg == "on") s = System.Text.RegularExpressions.Regex.Replace(s, "\"enabled\":\\s*(true|false)", "\"enabled\": true");
        else if (arg == "off") s = System.Text.RegularExpressions.Regex.Replace(s, "\"enabled\":\\s*(true|false)", "\"enabled\": false");
        else if (System.Text.RegularExpressions.Regex.IsMatch(arg, "^\\d{1,2}:\\d{2}$")) {
            var parts = arg.Split(':'); var tr = DateTime.UtcNow.AddHours(3);
            var until = new DateTime(tr.Year, tr.Month, tr.Day, int.Parse(parts[0]), int.Parse(parts[1]), 0);
            if (until < tr) until = until.AddDays(1);
            s = System.Text.RegularExpressions.Regex.Replace(s, "\"until\":\\s*\"[^\"]*\"", "\"until\": \"" + until.ToString("yyyy-MM-ddTHH:mm:ss", Rt.Inv) + "+03:00\"");
        } else { Console.WriteLine("  kullanım: bakim on | bakim off | bakim 22:00"); return; }
        File.WriteAllText(p, s); Console.WriteLine("  Bakım ayarı güncellendi: " + arg); Rt.Log("console: maint " + arg);
    }
    static void Players() {
        long now = Rt.Clock.ElapsedMilliseconds;
        var list = Rt.Clients.Values.OrderBy(c => c.Sid).ToList();
        Console.WriteLine("  Gerçek zamanlı bağlı: " + list.Count + "  |  Python oyunda: " + PyPlayers());
        foreach (var c in list)
            Console.WriteLine(string.Format(Rt.Inv, "  ID {0,-4} karakter {1,-6} konum ({2,7:0},{3,7:0},{4,5:0})  son veri {5,5} ms  mesaj {6}  gönderilen {7}  atlanan {8}",
                c.Sid, c.Cid, c.P[0], c.P[1], c.P[2], c.PAt > 0 ? (now - c.PAt).ToString(Rt.Inv) : "-", c.Msgs, c.Sent, c.Dropped));
    }
    static void Help() {
        Console.WriteLine("  Komutlar:");
        Console.WriteLine("    oyuncular            bağlı oyuncular ve son veri yaşı");
        Console.WriteLine("    durum                sayaçlar (mesaj/sn, oyuncu sayıları)");
        Console.WriteLine("    duyuru <metin>       tüm oyunculara ekran duyurusu");
        Console.WriteLine("    bakim on|off|22:00   bakım sayfasını aç/kapat veya açılış saatini ayarla");
        Console.WriteLine("    restart oyun         Python oyun sunucusunu yeniden başlat");
        Console.WriteLine("    temizle              ekranı temizle");
        Console.WriteLine("    cikis                bu konsolu kapat (oyun sunucusu çalışmaya devam eder)");
    }
    static void TitleLoop() {
        long lastIn = 0, lastOut = 0;
        while (true) {
            Thread.Sleep(2000);
            long i = Interlocked.Read(ref Rt.MsgsIn), o = Interlocked.Read(ref Rt.MsgsOut);
            int py = PyPlayers();
            try { string rtc = Rt.Clients.Count.ToString(Rt.Inv); if (Remote) { string s = Admin("/rt/status"); int k = s.IndexOf("\"connected\":"); rtc = k < 0 ? "?" : new string(s.Substring(k + 12).TakeWhile(char.IsDigit).ToArray()); } Console.Title = "PAVCITY Sunucu  |  Oyunda: " + (py < 0 ? "?" : py.ToString(Rt.Inv)) + "  |  Gerçek zamanlı: " + rtc + (Remote ? "" : "  |  giriş " + ((i - lastIn) / 2) + "/sn  çıkış " + ((o - lastOut) / 2) + "/sn"); } catch { }
            lastIn = i; lastOut = o;
        }
    }
    static int Main(string[] args) {
        Root = args.Length > 0 ? args[0] : Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", ".."));
        Rt.Root = Root;
        Console.OutputEncoding = Encoding.UTF8;
        string secretFile = Path.Combine(Root, "backups", "rt172.secret");
        if (!File.Exists(secretFile)) { var b = new byte[32]; using (var rng = RandomNumberGenerator.Create()) rng.GetBytes(b); File.WriteAllText(secretFile, Convert.ToBase64String(b)); }
        Rt.Secret = Convert.FromBase64String(File.ReadAllText(secretFile).Trim());
        bool headless = args.Contains("--headless");
        int port = 8090; foreach (var a in args) if (a.StartsWith("--port=")) port = int.Parse(a.Substring(7), Rt.Inv);
        ThreadPool.SetMinThreads(32, 32);
        var listener = new HttpListener(); listener.Prefixes.Add("http://127.0.0.1:" + port.ToString(Rt.Inv) + "/");
        bool remote = false; RemotePort = port;
        try { listener.Start(); } catch (Exception e) {
            if (headless) { Console.WriteLine("Gerçek zamanlı sunucu açılamadı (port " + port + "): " + e.Message); Rt.Log("start failed: " + e.Message); return 1; }
            remote = true; RemotePort = port;
        }
        if (remote) return Console_(true);
        Rt.Log("pavrt172 started on port " + port);
        new Thread(() => { while (true) { try { var ctx = listener.GetContext(); Task.Run(() => Rt.Serve(ctx)); } catch (Exception e) { Rt.Log("accept: " + e.Message); Thread.Sleep(50); } } }) { IsBackground = true, Name = "accept" }.Start();
        new Thread(() => {
            var sw = Stopwatch.StartNew(); long next = 0;
            while (true) {
                next += 66; long wait = next - sw.ElapsedMilliseconds; if (wait > 0) Thread.Sleep((int)wait); else if (wait < -500) next = sw.ElapsedMilliseconds;
                try { Rt.Broadcast(); } catch (Exception e) { Rt.Log("broadcast: " + e.Message); }
            }
        }) { IsBackground = true, Name = "broadcast", Priority = ThreadPriority.AboveNormal }.Start();
        if (headless) { Console.WriteLine("pavrt172 headless on port " + port); Thread.Sleep(Timeout.Infinite); return 0; }
        return Console_(false);
    }
    static int RemotePort = 8090; static bool Remote;
    static string Admin(string p) { try { var wc = new WebClient(); wc.Encoding = Encoding.UTF8; return wc.DownloadString("http://127.0.0.1:" + RemotePort.ToString(Rt.Inv) + p); } catch (Exception e) { return "  (gerçek zamanlı sunucuya ulaşılamadı: " + e.Message + ")"; } }
    static int Console_(bool remote) {
        Console.WriteLine("==============================================================");
        Console.WriteLine("  PAVCITY · Los Santos Roleplay  —  Sunucu Konsolu (172)");
        Console.WriteLine("==============================================================");
        Console.WriteLine(remote ? "  Arka planda çalışan gerçek zamanlı sunucuya bağlanıldı (127.0.0.1:" + RemotePort + ")." : "  Gerçek zamanlı sunucu bu pencerede çalışıyor: 127.0.0.1:" + RemotePort + "/rt");
        EnsureBackend(); EnsureTunnel();
        Remote = remote; new Thread(TitleLoop) { IsBackground = true }.Start();
        Help();
        while (true) {
            Console.Write("pavcity> ");
            string line = Console.ReadLine(); if (line == null) { Thread.Sleep(Timeout.Infinite); }
            line = line.Trim(); if (line == "") continue;
            string cmd = line.Split(' ')[0].ToLowerInvariant(); string rest = line.Length > cmd.Length ? line.Substring(cmd.Length).Trim() : "";
            try {
                if (cmd == "oyuncular" || cmd == "players") { if (remote) { Console.WriteLine("  Python oyunda: " + PyPlayers()); Console.Write(Admin("/rt/admin/players")); } else Players(); }
                else if (cmd == "durum" || cmd == "status") Console.WriteLine("  " + (remote ? Admin("/rt/status") : Rt.StatusJson()) + "  python_oyuncu=" + PyPlayers());
                else if (cmd == "duyuru" || cmd == "say") { if (rest == "") Console.WriteLine("  kullanım: duyuru <metin>"); else if (remote) { Console.WriteLine(Admin("/rt/admin/say?m=" + Uri.EscapeDataString(rest)) == "ok" ? "  Duyuru gönderildi." : "  Duyuru gönderilemedi."); } else { Rt.Notice = rest.Length > 200 ? rest.Substring(0, 200) : rest; Rt.NoticeAt = Rt.Clock.ElapsedMilliseconds; Rt.Log("console: say " + rest); Console.WriteLine("  Duyuru gönderildi."); } }
                else if (cmd == "bakim" || cmd == "maint") Maint(rest.ToLowerInvariant());
                else if (cmd == "restart" && (rest == "oyun" || rest == "backend")) RestartBackend();
                else if (cmd == "temizle" || cmd == "cls") Console.Clear();
                else if (cmd == "cikis" || cmd == "exit" || cmd == "quit") {
                    Console.WriteLine(remote ? "  Konsol kapanıyor; arka plandaki sunucular çalışmaya devam ediyor." : "  Konsol kapanıyor. Bu penceredeki gerçek zamanlı sunucu da kapanır; oyun eski yöntemle (HTTP) devam eder.");
                    return 0;
                }
                else if (cmd == "yardim" || cmd == "help" || cmd == "?") Help();
                else Console.WriteLine("  Bilinmeyen komut. 'yardim' yaz.");
            } catch (Exception e) { Console.WriteLine("  Hata: " + e.Message); }
        }
    }
}
