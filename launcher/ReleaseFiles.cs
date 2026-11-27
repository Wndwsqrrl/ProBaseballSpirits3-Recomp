using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Web.Script.Serialization;

namespace ProSpi3Launcher
{
    public sealed class MissingRuntimeException : IOException
    { public MissingRuntimeException() : base("Install the Microsoft Visual C++ x64 Runtime, then try again. Use the runtime link below.") { } }
    public sealed class Settings
    {
        public string GameFolder { get; set; }
        public string Language { get; set; }
        public string Resolution { get; set; }
        public int RenderScale { get; set; }
        public Settings() { GameFolder = ""; Language = "English"; Resolution = "720p"; RenderScale = 1; }
    }

    public sealed class LaunchPlan
    {
        public string Executable { get; set; }
        public string WorkingDirectory { get; set; }
        public string Arguments { get; set; }
        public string GameFolder { get; set; }
        public string UserDataFolder { get; set; }
        public Dictionary<string, string> Environment { get; set; }
    }

    public static class ReleaseFiles
    {
        public const string ExpectedXex = "903e2e94188da3525c9ca39b9f8d9f27c3f6beee25b93a48c90921cda3d8cdc0";
        public static readonly string Root = AppDomain.CurrentDomain.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar);
        public static readonly string Local = Path.Combine(Root, "local");
        public static readonly JavaScriptSerializer Json = new JavaScriptSerializer();
        public static void Log(string message)
        {
            try { Directory.CreateDirectory(Local); File.AppendAllText(Path.Combine(Local, "launcher.log"), DateTime.UtcNow.ToString("o") + " " + message + System.Environment.NewLine); }
            catch (IOException) { }
            catch (UnauthorizedAccessException) { }
        }

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern bool CreateHardLink(string destination, string source, IntPtr security);

        private static void CheckCancel(Func<bool> cancel) { if (cancel()) throw new OperationCanceledException(); }
        private static string Hex(byte[] value) { return BitConverter.ToString(value).Replace("-", "").ToLowerInvariant(); }
        public static string HashFile(string path, Func<bool> cancel)
        {
            using (var stream = File.OpenRead(path))
            using (var hash = SHA256.Create())
            {
                var buffer = new byte[1024 * 1024]; int count;
                while ((count = stream.Read(buffer, 0, buffer.Length)) != 0)
                { CheckCancel(cancel); hash.TransformBlock(buffer, 0, count, buffer, 0); }
                hash.TransformFinalBlock(new byte[0], 0, 0); return Hex(hash.Hash);
            }
        }
        private static byte[] Exact(BinaryReader reader, int length)
        {
            var result = reader.ReadBytes(length);
            if (result.Length != length) throw new InvalidDataException("The English patch is incomplete.");
            return result;
        }
        private static uint BigWord(byte[] bytes, int offset)
        { return (uint)bytes[offset] << 24 | (uint)bytes[offset + 1] << 16 | (uint)bytes[offset + 2] << 8 | bytes[offset + 3]; }
        private static string Canonical(string path) { return Path.GetFullPath(path).TrimEnd('\\', '/'); }
        private static bool Within(string path, string folder)
        { return path.Equals(folder, StringComparison.OrdinalIgnoreCase) || path.StartsWith(folder + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase); }
        private static void PlainDestination(string path)
        {
            for (var directory = new DirectoryInfo(Path.GetDirectoryName(Path.GetFullPath(path))); directory != null; directory = directory.Parent)
                if (directory.Exists && (directory.Attributes & FileAttributes.ReparsePoint) != 0)
                    throw new IOException("The preview output folder must not use a directory link.");
        }

        public static string ValidateGame(string folder, Func<bool> cancel)
        {
            var full = Path.GetFullPath(folder);
            if (full.TrimEnd('\\', '/').Equals(Path.GetPathRoot(full).TrimEnd('\\', '/'), StringComparison.OrdinalIgnoreCase))
                throw new IOException("Choose the game's own extracted folder, not an entire drive.");
            var root = Canonical(full);
            var xex = Path.Combine(root, "default.xex");
            if (!File.Exists(xex) || !File.Exists(Path.Combine(root, "cdvdroot", "baseball.fbd")))
                throw new IOException("Choose the extracted game folder containing default.xex and cdvdroot/baseball.fbd.");
            if (HashFile(xex, cancel) != ExpectedXex)
                throw new InvalidDataException("This game version is not supported. Use the original Japanese Xbox 360 release.");
            return root;
        }

        private static byte[] DecodeCmp(byte[] data, Func<bool> cancel)
        {
            if (data.Length < 4 || Encoding.ASCII.GetString(data, 0, 4) != "CMP\0") return data;
            if (data.Length < 18 || Encoding.ASCII.GetString(data, 0, 8) != "CMP\0L\0\0B" || data[12] != 'H' || data[13] != 'S')
                throw new InvalidDataException("Unsupported compressed game resource.");
            uint expected = BitConverter.ToUInt32(data, 8);
            if (expected == 0 || expected > 64 * 1024 * 1024 || expected != BigWord(data, 14))
                throw new InvalidDataException("Invalid compressed resource size.");
            var output = new byte[(int)expected]; var ring = new byte[4096]; int position = 0, cursor = 18;
            Func<byte> next = delegate { if (cursor >= data.Length) throw new InvalidDataException("Truncated game resource."); return data[cursor++]; };
            while (position < output.Length)
            {
                CheckCancel(cancel); int flags = next();
                for (int bit = 0; bit < 8 && position < output.Length; ++bit)
                {
                    int start = position;
                    if ((flags & (1 << bit)) != 0)
                    {
                        int low = next(), high = next(), offset = low | ((high & 0xF0) << 4), count = (high & 15) + 3;
                        if (start + count > output.Length) throw new InvalidDataException("Compressed resource exceeds its size.");
                        for (int i = 0; i < count; ++i)
                        { byte value = ring[(start + offset + i) & 4095]; ring[(start - 18 + i) & 4095] = value; output[position++] = value; }
                    }
                    else { byte value = next(); ring[(start - 18) & 4095] = value; output[position++] = value; }
                }
            }
            return output;
        }

        public static void ApplyArchivePatch(string original, string destination, string patchPath,
                                             Action<int, string> progress, Func<bool> cancel)
        {
            original = Path.GetFullPath(original); destination = Path.GetFullPath(destination);
            if (original.Equals(destination, StringComparison.OrdinalIgnoreCase)) throw new IOException("Original and English archives must be separate.");
            PlainDestination(destination); Directory.CreateDirectory(Path.GetDirectoryName(destination));
            var temporary = destination + ".building-" + Guid.NewGuid().ToString("N");
            try
            {
                using (var compressed = File.OpenRead(patchPath))
                using (var gzip = new GZipStream(compressed, CompressionMode.Decompress))
                using (var patch = new BinaryReader(gzip))
                {
                    if (Encoding.ASCII.GetString(Exact(patch, 8)) != "P3ENG001") throw new InvalidDataException("Unknown English patch format.");
                    long sourceSize = checked((long)patch.ReadUInt64()); string sourceHash = Hex(Exact(patch, 32));
                    long targetSize = checked((long)patch.ReadUInt64()); string targetHash = Hex(Exact(patch, 32));
                    int directorySize = checked((int)patch.ReadUInt32());
                    if (directorySize < 16 || directorySize > 32 * 1024 * 1024 || targetSize < directorySize)
                        throw new InvalidDataException("Invalid patch directory.");
                    var directory = Exact(patch, directorySize); int count = checked((int)patch.ReadUInt32());
                    if (Encoding.ASCII.GetString(directory, 0, 4) != "BNDR" || count < 1 || count > 100000 ||
                        BigWord(directory, 12) != count || 16L + count * 268L > directorySize)
                        throw new InvalidDataException("Invalid patch member table.");
                    progress(2, "Checking the original game archive...");
                    if (new FileInfo(original).Length != sourceSize || HashFile(original, cancel) != sourceHash)
                        throw new InvalidDataException("The game archive differs from the supported original. English setup stopped without changing it.");
                    using (var source = File.OpenRead(original))
                    using (var output = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
                    {
                        output.SetLength(targetSize); output.Write(directory, 0, directory.Length); long previousEnd = directorySize;
                        var buffer = new byte[1024 * 1024];
                        for (int index = 0; index < count; ++index)
                        {
                            CheckCancel(cancel);
                            long sourceOffset = checked((long)patch.ReadUInt64()); int oldSize = checked((int)patch.ReadUInt32());
                            long targetOffset = checked((long)patch.ReadUInt64()); int newSize = checked((int)patch.ReadUInt32()); int mode = patch.ReadByte();
                            long allocated = ((long)newSize + 2047) / 2048 * 2048;
                            if (sourceOffset < 0 || oldSize < 0 || sourceOffset > sourceSize - oldSize || newSize < 0 ||
                                targetOffset < previousEnd || targetOffset % 2048 != 0 || targetOffset > targetSize - allocated)
                                throw new InvalidDataException("Invalid patch member extent.");
                            int record = 16 + index * 268;
                            if ((long)BigWord(directory, record + 256) * 2048 != targetOffset || BigWord(directory, record + 260) != newSize || BigWord(directory, record + 264) != allocated)
                                throw new InvalidDataException("Patch member does not match its directory.");
                            source.Position = sourceOffset; output.Position = targetOffset;
                            if (mode == 0)
                            {
                                if (oldSize != newSize) throw new InvalidDataException("Invalid copied member size.");
                                int remaining = oldSize;
                                while (remaining > 0)
                                {
                                    CheckCancel(cancel); int n = source.Read(buffer, 0, Math.Min(buffer.Length, remaining));
                                    if (n == 0) throw new EndOfStreamException(); output.Write(buffer, 0, n); remaining -= n;
                                }
                            }
                            else if (mode == 1)
                            {
                                if (oldSize > 64 * 1024 * 1024 || newSize > 64 * 1024 * 1024)
                                    throw new InvalidDataException("Patched resource is too large.");
                                byte[] data;
                                using (var reader = new BinaryReader(source, Encoding.UTF8, true)) data = DecodeCmp(Exact(reader, oldSize), cancel);
                                if (data.Length != newSize) throw new InvalidDataException("Decoded resource size differs.");
                                for (int start = 0; start < data.Length; start += buffer.Length)
                                {
                                    CheckCancel(cancel); int n = Math.Min(buffer.Length, data.Length - start); var delta = Exact(patch, n);
                                    for (int j = 0; j < n; ++j) data[start + j] ^= delta[j];
                                }
                                output.Write(data, 0, data.Length);
                            }
                            else throw new InvalidDataException("Unknown patch operation.");
                            previousEnd = targetOffset + allocated;
                            if (index % 40 == 0) progress(10 + index * 75 / count, "Preparing English files... " + (index + 1) + " / " + count);
                        }
                        if (previousEnd != targetSize || gzip.ReadByte() != -1) throw new InvalidDataException("Unexpected patch extent.");
                        output.Flush(true);
                    }
                    progress(90, "Verifying the English archive...");
                    if (HashFile(temporary, cancel) != targetHash) throw new InvalidDataException("English verification failed. The original files are unchanged.");
                    CheckCancel(cancel);
                    if (File.Exists(destination)) File.Replace(temporary, destination, destination + ".previous-" + Guid.NewGuid().ToString("N"));
                    else File.Move(temporary, destination);
                }
            }
            finally { if (File.Exists(temporary)) File.Delete(temporary); }
        }

        public static string PrepareEnglish(string originalRoot, Action<int, string> progress, Func<bool> cancel)
        {
            var patch = Path.Combine(Root, "assets", "english-assets.p3patch");
            if (!File.Exists(patch)) throw new FileNotFoundException("The English patch is missing. Extract the complete preview package.");
            string folderId;
            using (var hash = SHA256.Create()) folderId = Hex(hash.ComputeHash(Encoding.UTF8.GetBytes(Canonical(originalRoot).ToUpperInvariant()))).Substring(0, 12);
            var english = Path.Combine(Local, "english-disc-" + folderId);
            if (Within(Canonical(english), Canonical(originalRoot)) || Within(Canonical(originalRoot), Canonical(english)))
                throw new IOException("Keep your original game folder separate from the preview's generated English folder.");
            var archive = Path.Combine(originalRoot, "cdvdroot", "baseball.fbd");
            var target = Path.Combine(english, "cdvdroot", "baseball.fbd");
            var stampFile = Path.Combine(english, "installation.json"); var sourceInfo = new FileInfo(archive);
            var identity = HashFile(patch, cancel) + ":" + sourceInfo.Length + ":" + sourceInfo.LastWriteTimeUtc.Ticks;
            bool archiveReady = false;
            if (File.Exists(stampFile) && File.Exists(target))
            {
                try
                {
                    var stamp = Json.Deserialize<Dictionary<string, string>>(File.ReadAllText(stampFile)); var info = new FileInfo(target);
                    archiveReady = stamp["identity"] == identity && stamp["output"] == info.Length + ":" + info.LastWriteTimeUtc.Ticks;
                }
                catch (Exception) { /* Rebuild an incomplete or outdated installation. */ }
            }
            PlainDestination(target);
            if (!archiveReady) ApplyArchivePatch(archive, target, patch, progress, cancel);
            foreach (var path in Directory.GetFiles(originalRoot, "*", SearchOption.AllDirectories))
            {
                CheckCancel(cancel); if (path.Equals(archive, StringComparison.OrdinalIgnoreCase)) continue;
                var relative = path.Substring(Canonical(originalRoot).Length + 1); var destination = Path.Combine(english, relative);
                PlainDestination(destination); Directory.CreateDirectory(Path.GetDirectoryName(destination));
                if (!File.Exists(destination) && !CreateHardLink(destination, path, IntPtr.Zero)) File.Copy(path, destination);
            }
            var completed = new FileInfo(target);
            File.WriteAllText(stampFile, Json.Serialize(new Dictionary<string, string> {
                { "identity", identity }, { "output", completed.Length + ":" + completed.LastWriteTimeUtc.Ticks } }));
            return english;
        }

        public static string Quote(string value)
        {
            var result = new StringBuilder("\""); int slashes = 0;
            foreach (char c in value)
            {
                if (c == '\\') { ++slashes; continue; }
                result.Append('\\', c == '"' ? slashes * 2 + 1 : slashes); result.Append(c); slashes = 0;
            }
            return result.Append('\\', slashes * 2).Append('"').ToString();
        }
        public static LaunchPlan MakePlan(Settings settings, string gameFolder)
        {
            if (settings.Language != "English" && settings.Language != "Japanese") throw new ArgumentException("Choose English or Japanese.");
            if (Array.IndexOf(new[] { "720p", "1080p", "1440p", "2160p" }, settings.Resolution) < 0 || settings.RenderScale < 1 || settings.RenderScale > 3)
                throw new ArgumentException("Choose a supported graphics setting.");
            var exe = Path.Combine(Root, "bin", "prospi3.exe");
            if (!File.Exists(exe)) exe = Path.Combine(Root, "prospi3-recomp", "out", "build", "win-amd64-release", "prospi3.exe");
            if (!File.Exists(exe)) throw new FileNotFoundException("The game executable is missing. Extract the complete preview package.");
            var language = settings.Language.ToLowerInvariant(); var userdata = Path.Combine(Local, "userdata", language); var cache = Path.Combine(Local, "cache", language);
            Directory.CreateDirectory(userdata); Directory.CreateDirectory(cache);
            return new LaunchPlan { Executable = exe, WorkingDirectory = Path.GetDirectoryName(exe), GameFolder = gameFolder, UserDataFolder = userdata,
                Arguments = Quote("--game_data_root=" + gameFolder) + " " + Quote("--user_data_root=" + userdata) + " " + Quote("--cache_root=" + cache) +
                    " --gpu_backend=d3d12 --render_target_path_d3d12=rov --mnk_mode=true --resolution=" + settings.Resolution + " --resolution_scale=" + settings.RenderScale,
                Environment = new Dictionary<string, string> { { "PROSPI3_ENGLISH", settings.Language == "English" ? "1" : "0" },
                    { "PROSPI3_PROFILE", "0" }, { "PROSPI3_TRACE_TEXT", "0" }, { "PROSPI3_RELOCATE_TEXT", "0" },
                    { "PROSPI3_LATIN_FONT", "1" }, { "PROSPI3_PROFILE_LABEL", language } } };
        }
        public static Process StartGame(LaunchPlan plan)
        {
            CheckRuntime(plan.WorkingDirectory, File.Exists);
            var start = new ProcessStartInfo(plan.Executable, plan.Arguments) { WorkingDirectory = plan.WorkingDirectory, UseShellExecute = false, CreateNoWindow = true };
            foreach (var pair in plan.Environment) start.EnvironmentVariables[pair.Key] = pair.Value;
            return Process.Start(start);
        }
        public static void CheckRuntime(string bin, Func<string, bool> exists)
        {
            foreach (var name in new[] { "MSVCP140.dll", "MSVCP140_ATOMIC_WAIT.dll", "VCRUNTIME140.dll", "VCRUNTIME140_1.dll" })
                if (!exists(Path.Combine(bin, name)) && !exists(Path.Combine(Environment.SystemDirectory, name))) throw new MissingRuntimeException();
        }
    }
}
