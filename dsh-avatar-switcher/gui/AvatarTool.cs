using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Net;
using System.Text;
using System.Text.RegularExpressions;
using System.Windows.Forms;

namespace DshAvatar
{
    class AvatarTool : Form
    {
        PictureBox pic;
        Label status;
        string picked = "";
        string dataDir = null;
        int port = 0;
        Random rnd = new Random();

        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new AvatarTool());
        }

        AvatarTool()
        {
            Text = "DSH 头像切换器";
            ClientSize = new Size(580, 400);
            StartPosition = FormStartPosition.CenterScreen;
            BackColor = Color.FromArgb(22, 22, 30);
            ForeColor = Color.Gainsboro;
            Font = new Font("Microsoft YaHei UI", 9F);

            pic = new PictureBox();
            pic.Left = 16; pic.Top = 16; pic.Width = 200; pic.Height = 200;
            pic.SizeMode = PictureBoxSizeMode.Zoom;
            pic.BackColor = Color.FromArgb(14, 14, 20);
            pic.BorderStyle = BorderStyle.FixedSingle;
            Controls.Add(pic);

            status = new Label();
            status.Left = 16; status.Top = 232; status.Width = 548; status.Height = 152;
            status.Text = "选一张图，再按下面的按钮。改完刷新界面（F5）。";
            Controls.Add(status);

            int x = 232, y = 16;
            AddBtn("选图...", x, y, 150, 34, delegate { PickFile(); }); y += 42;
            AddBtn("设为「我」", x, y, 150, 34, delegate { Apply("user"); }); y += 42;
            AddBtn("设为「助手」", x, y, 150, 34, delegate { Apply("ai"); }); y += 42;
            AddBtn("设为立绘", x, y, 150, 34, delegate { Apply("mascot"); }); y += 42;
            AddBtn("检查连接", x, y, 150, 34, delegate { Probe(true); }); y += 42;
            AddBtn("打开头像目录", x, y, 150, 34, delegate { OpenDir(); });
            AddBtn("去背景", x + 160, 16, 150, 34, delegate { Cutout(); });
            AddBtn("恢复默认立绘", x + 160, 58, 150, 34, delegate { ResetMascot(); });

            Load += delegate { Probe(false); };
        }

        void AddBtn(string text, int x, int y, int w, int h, EventHandler onClick)
        {
            Button b = new Button();
            b.Text = text; b.Left = x; b.Top = y; b.Width = w; b.Height = h;
            b.FlatStyle = FlatStyle.Flat;
            b.BackColor = Color.FromArgb(38, 38, 52);
            b.ForeColor = Color.Gainsboro;
            b.FlatAppearance.BorderColor = Color.FromArgb(70, 70, 96);
            b.Click += onClick;
            Controls.Add(b);
        }

        void Say(string s)
        {
            status.Text = s;
            Application.DoEvents();
        }

        static string Rand()
        {
            string a = "abcdefghijklmnopqrstuvwxyz0123456789";
            Random r = new Random(Guid.NewGuid().GetHashCode());
            char[] c = new char[6];
            for (int i = 0; i < 6; i++) c[i] = a[r.Next(a.Length)];
            return new string(c);
        }

        string FindDataDir()
        {
            List<string> cand = new List<string>();
            string home = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
            string a = Path.Combine(home, ".dsh-wallpaper-engine");
            if (Directory.Exists(a)) cand.Add(a);
            string b = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "dsh-wallpaper-engine");
            if (Directory.Exists(b)) cand.Add(b);
            try
            {
                foreach (string d in Directory.GetDirectories(home, "*wallpaper-engine*"))
                    if (Directory.Exists(Path.Combine(d, "avatars")) || Directory.Exists(Path.Combine(d, "mascot"))) cand.Add(d);
            }
            catch { }
            if (cand.Count > 0) return cand[0];
            return null;
        }

        List<int> ListeningPorts()
        {
            List<int> res = new List<int>();
            try
            {
                ProcessStartInfo psi = new ProcessStartInfo("netstat", "-ano");
                psi.UseShellExecute = false;
                psi.RedirectStandardOutput = true;
                psi.CreateNoWindow = true;
                Process p = Process.Start(psi);
                string outp = p.StandardOutput.ReadToEnd();
                p.WaitForExit(4000);
                foreach (string line in outp.Split('\n'))
                {
                    if (line.IndexOf("LISTENING") < 0) continue;
                    Match m = Regex.Match(line, @"127\.0\.0\.1:(\d+)\s|0\.0\.0\.0:(\d+)\s");
                    if (!m.Success) continue;
                    string g = m.Groups[1].Success ? m.Groups[1].Value : m.Groups[2].Value;
                    int v;
                    if (int.TryParse(g, out v) && !res.Contains(v)) res.Add(v);
                }
            }
            catch { }
            return res;
        }

        string Http(string url, string method, string body, int timeoutMs)
        {
            try
            {
                HttpWebRequest req = (HttpWebRequest)WebRequest.Create(url);
                req.Method = method;
                req.Timeout = timeoutMs;
                req.ReadWriteTimeout = timeoutMs;
                req.Proxy = null;
                req.KeepAlive = false;
                if (body != null)
                {
                    byte[] bb = Encoding.UTF8.GetBytes(body);
                    req.ContentType = "application/json";
                    req.ContentLength = bb.Length;
                    using (Stream s = req.GetRequestStream()) s.Write(bb, 0, bb.Length);
                }
                using (HttpWebResponse r = (HttpWebResponse)req.GetResponse())
                using (StreamReader sr = new StreamReader(r.GetResponseStream(), Encoding.UTF8))
                    return sr.ReadToEnd();
            }
            catch { return null; }
        }

        int Probe(bool verbose)
        {
            if (dataDir == null) dataDir = FindDataDir();
            List<int> ports = ListeningPorts();
            foreach (int pt in ports)
            {
                string r = Http("http://127.0.0.1:" + pt + "/wallpaper-engine/settings", "GET", null, 400);
                if (r != null && r.IndexOf("settings", StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    port = pt;
                    if (verbose) Say("GUI 找到：端口 " + pt + "\n数据目录：" + dataDir);
                    return pt;
                }
            }
            port = 0;
            if (verbose) Say("没探到 GUI。先确认 DSH 桌面端开着，再点检查连接。");
            return 0;
        }

        void PickFile()
        {
            OpenFileDialog d = new OpenFileDialog();
            d.Filter = "图片|*.png;*.jpg;*.jpeg;*.webp;*.bmp";
            if (d.ShowDialog() != DialogResult.OK) return;
            picked = d.FileName;
            try
            {
                using (Image img = Image.FromFile(picked))
                    pic.Image = new Bitmap(img);
                Say("已选：" + Path.GetFileName(picked) + "\n" + Image.FromFile(picked).Width + "x" + Image.FromFile(picked).Height);
            }
            catch (Exception e) { Say("读图失败：" + e.Message); }
        }

        string NormalizeImage(string path)
        {
            string ext = Path.GetExtension(path).ToLowerInvariant();
            if (ext == ".png" || ext == ".jpg" || ext == ".jpeg" || ext == ".webp")
                return path;
            Bitmap bmp = new Bitmap(Image.FromFile(path));
            string tmp = Path.Combine(Path.GetTempPath(), "dshav_" + Rand() + ".png");
            bmp.Save(tmp, System.Drawing.Imaging.ImageFormat.Png);
            bmp.Dispose();
            return tmp;
        }

        void Apply(string kind)
        {
            if (picked.Length == 0) { Say("先点「选图...」。"); return; }
            if (dataDir == null) dataDir = FindDataDir();
            if (dataDir == null) { Say("找不到 .dsh-wallpaper-engine 数据目录。"); return; }
            if (port == 0 && Probe(true) == 0) return;

            string src = NormalizeImage(picked);
            string ext = Path.GetExtension(src).ToLowerInvariant();
            if (ext == ".jpeg") ext = ".jpg";
            string name;
            string sub;
            if (kind == "mascot") { sub = "mascot"; name = "mascot-" + Rand() + ext; }
            else { sub = "avatars"; name = kind + "-" + Rand() + ext; }

            string dir = Path.Combine(dataDir, sub);
            Directory.CreateDirectory(dir);
            string dst = Path.Combine(dir, name);
            try { File.Copy(src, dst, true); }
            catch (Exception e) { Say("写入失败：" + e.Message); return; }

            string body;
            if (kind == "user") body = "{\"avatarUserImage\":\"" + name + "\",\"avatarEnabled\":true}";
            else if (kind == "ai") body = "{\"avatarAiImage\":\"" + name + "\",\"avatarEnabled\":true}";
            else
            {
                int w = 96, h = 102;
                try
                {
                    using (Image img = Image.FromFile(src))
                        h = (int)Math.Round(96.0 * img.Height / img.Width);
                }
                catch { }
                if (h < 1) h = 1;
                if (h > 192) h = 192;
                body = "{\"mascotImage\":\"" + name + "\",\"mascotImageBox\":\"96x" + h + "\"}";
            }

            string resp = Http("http://127.0.0.1:" + port + "/wallpaper-engine/settings", "PUT", body, 3000);
            if (resp == null) { Say("PUT 失败：端口 " + port + " 没响应。"); return; }

            string url = "http://127.0.0.1:" + port + "/wallpaper-engine/" + (kind == "mascot" ? "mascot" : "avatar/" + kind);
            string chk = Http(url, "GET", null, 1500);

            Say("装好了：" + name + "\n落到 " + dst + "\n" +
                (chk != null ? "接口校验通过，回显 " + chk.Length + " 字节" : "接口没回显，刷新页面看效果") +
                "\n\n回 GUI 按 F5 生效。");
        }

        void ResetMascot()
        {
            if (port == 0 && Probe(true) == 0) return;
            string r = Http("http://127.0.0.1:" + port + "/wallpaper-engine/settings", "PUT",
                "{\"mascotImage\":\"\",\"mascotImageBox\":\"\"}", 3000);
            Say(r == null ? "PUT 失败。" : "立绘已切回内置，F5 生效。");
        }

        void OpenDir()
        {
            if (dataDir == null) dataDir = FindDataDir();
            if (dataDir == null) { Say("没找到数据目录。"); return; }
            Process.Start("explorer.exe", dataDir);
        }

        void Cutout()
        {
            if (picked.Length == 0) { Say("先点「选图...」。"); return; }
            string py = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
                @".dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe");
            string script = Path.Combine(Path.GetDirectoryName(picked), "cutout.py");
            if (!File.Exists(py)) { Say("本机没找到 python 运行时：\n" + py); return; }
            if (!File.Exists(script)) { Say("把 cutout.py 放到图片同目录再点。\n" + script); return; }
            string outp = Path.Combine(Path.GetDirectoryName(picked), Path.GetFileNameWithoutExtension(picked) + "_cut.png");
            ProcessStartInfo psi = new ProcessStartInfo(py, "\"" + script + "\" \"" + picked + "\" -o \"" + outp + "\"");
            psi.UseShellExecute = false; psi.CreateNoWindow = true; psi.RedirectStandardOutput = true; psi.RedirectStandardError = true;
            Process p = Process.Start(psi);
            string so = p.StandardOutput.ReadToEnd() + p.StandardError.ReadToEnd();
            p.WaitForExit(120000);
            if (File.Exists(outp)) { picked = outp; pic.Image = new Bitmap(Image.FromFile(outp)); Say("去背景完成：\n" + outp); }
            else Say("去背景没出文件。\n" + so);
        }
    }
}
