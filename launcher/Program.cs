using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Windows.Forms;

[assembly: AssemblyTitle("ProSpi3 Launcher")]
[assembly: AssemblyProduct("Pro Yakyuu Spirits 3 Recomp")]
[assembly: AssemblyVersion("0.1.0.0")]
[assembly: AssemblyFileVersion("0.1.0.1")]
[assembly: AssemblyCopyright("Copyright 2026 Wndwsqrrl")]

namespace ProSpi3Launcher
{
    static class Program
    {
        [STAThread]
        static int Main(string[] args)
        {
            try
            {
                if (args.Length > 0 && args[0] == "--verify-patch")
                {
                    if (args.Length != 4) return 2;
                    var timer = Stopwatch.StartNew();
                    ReleaseFiles.ApplyArchivePatch(args[1], args[2], Path.Combine(ReleaseFiles.Root, "assets", "english-assets.p3patch"), delegate { }, delegate { return false; });
                    File.WriteAllText(args[3], ReleaseFiles.Json.Serialize(new {
                        verified = true, elapsed_seconds = timer.Elapsed.TotalSeconds,
                        output_sha256 = ReleaseFiles.HashFile(args[2], delegate { return false; }), game_launched = false }));
                    return 0;
                }
                if (args.Length > 0 && args[0] == "--self-test")
                {
                    if (args.Length != 2) return 2;
                    var settings = new Settings();
                    if (settings.Language != "English" || settings.RenderScale != 1 || settings.Resolution != "720p") throw new Exception("Default settings differ.");
                    settings.GameFolder = Path.Combine(ReleaseFiles.Root, "original game");
                    var english = ReleaseFiles.MakePlan(settings, Path.Combine(ReleaseFiles.Local, "english test"));
                    settings.Language = "Japanese";
                    var japanese = ReleaseFiles.MakePlan(settings, settings.GameFolder);
                    if (english.Environment["PROSPI3_ENGLISH"] != "1" || japanese.Environment["PROSPI3_ENGLISH"] != "0" ||
                        english.UserDataFolder == japanese.UserDataFolder || english.GameFolder == japanese.GameFolder ||
                        english.Arguments.Contains("d3d12_adapter=1") || japanese.Arguments.Contains("d3d12_adapter=1") ||
                        english.Environment["PROSPI3_RELOCATE_TEXT"] != "0" || japanese.Environment["PROSPI3_RELOCATE_TEXT"] != "0")
                        throw new Exception("Language isolation or launch flags differ.");
                    if (ReleaseFiles.Quote("a b") != "\"a b\"" || ReleaseFiles.Quote("C:\\game\\") != "\"C:\\game\\\\\"") throw new Exception("Argument quoting differs.");
                    bool rejected = false;
                    try { settings.Language = "invalid"; ReleaseFiles.MakePlan(settings, settings.GameFolder); }
                    catch (ArgumentException) { rejected = true; }
                    if (!rejected) throw new Exception("Invalid language was accepted.");
                    bool missingRuntime = false;
                    try { ReleaseFiles.CheckRuntime(english.WorkingDirectory, delegate { return false; }); }
                    catch (MissingRuntimeException) { missingRuntime = true; }
                    if (!missingRuntime) throw new Exception("Missing runtime was not detected.");
                    ReleaseFiles.CheckRuntime(english.WorkingDirectory, File.Exists);
                    bool driveRejected = false;
                    try { ReleaseFiles.ValidateGame(Path.GetPathRoot(ReleaseFiles.Root), delegate { return false; }); }
                    catch (IOException) { driveRejected = true; }
                    if (!driveRejected) throw new Exception("A whole drive was accepted as a game folder.");
                    File.WriteAllText(args[1], ReleaseFiles.Json.Serialize(new { defaults_verified = true, both_languages_verified = true,
                        separate_profiles_verified = true, arguments_verified = true, invalid_settings_rejected = true, runtime_check_verified = true, drive_root_rejected = true, game_launched = false }));
                    return 0;
                }
                if (args.Length > 0 && args[0] == "--test-cancel")
                {
                    if ((args.Length != 4 && args.Length != 5) || File.Exists(args[2])) return 2;
                    bool requested = false, cancelled = false;
                    try { ReleaseFiles.ApplyArchivePatch(args[1], args[2], args.Length == 5 ? args[4] : Path.Combine(ReleaseFiles.Root, "assets", "english-assets.p3patch"),
                        delegate(int value, string text) { if (value >= 10) requested = true; }, delegate { return requested; }); }
                    catch (OperationCanceledException) { cancelled = true; }
                    if (!cancelled || File.Exists(args[2]) || Directory.GetFiles(Path.GetDirectoryName(args[2]), Path.GetFileName(args[2]) + ".building-*").Length != 0)
                        throw new Exception("Cancellation did not clean up its temporary output.");
                    File.WriteAllText(args[3], ReleaseFiles.Json.Serialize(new { cancellation_verified = true, temporary_output_removed = true, game_launched = false }));
                    return 0;
                }
                if (args.Length > 0 && args[0] == "--check-install")
                {
                    if (args.Length != 3) return 2;
                    var game = ReleaseFiles.ValidateGame(args[1], delegate { return false; });
                    var english = ReleaseFiles.PrepareEnglish(game, delegate { }, delegate { return false; });
                    File.WriteAllText(args[2], ReleaseFiles.Json.Serialize(new { installation_verified = true,
                        english_archive_sha256 = ReleaseFiles.HashFile(Path.Combine(english, "cdvdroot", "baseball.fbd"), delegate { return false; }), game_launched = false }));
                    return 0;
                }
                Application.EnableVisualStyles(); Application.SetCompatibleTextRenderingDefault(false);
                if (args.Length == 2 && args[0] == "--preview")
                {
                    using (var form = new LauncherForm())
                    using (var image = new Bitmap(form.Width, form.Height))
                    {
                        PreparePreview(form); Application.DoEvents();
                        form.DrawToBitmap(image, new Rectangle(Point.Empty, form.Size));
                        PaintPreviewChoices(form, image, form);
                        image.Save(args[1]);
                        var controls = new System.Collections.Generic.List<object>(); DescribeControls(form, controls);
                        File.WriteAllText(args[1] + ".layout.json", ReleaseFiles.Json.Serialize(controls));
                    }
                    return 0;
                }
                if (args.Length != 0) return 2;
                Application.Run(new LauncherForm()); return 0;
            }
            catch (Exception error)
            {
                if (args.Length > 0)
                {
                    Directory.CreateDirectory(ReleaseFiles.Local);
                    File.WriteAllText(Path.Combine(ReleaseFiles.Local, "launcher-check-error.txt"), error.ToString());
                }
                else MessageBox.Show(error.Message, "ProSpi3 Launcher", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return 1;
            }
        }
        static void PreparePreview(Control control)
        {
            var handle = control.Handle;
            control.PerformLayout();
            foreach (Control child in control.Controls) PreparePreview(child);
            control.PerformLayout();
        }
        static void DescribeControls(Control control, System.Collections.Generic.List<object> result)
        {
            result.Add(new { type = control.GetType().Name, text = control.Text, bounds = control.Bounds.ToString(), client = control.ClientSize.ToString() });
            foreach (Control child in control.Controls) DescribeControls(child, result);
        }
        // Win32 combo boxes omit selected text from an unshown DrawToBitmap.
        // Fill that preview-only gap from the actual control values and bounds.
        static void PaintPreviewChoices(Control control, Bitmap image, Form form)
        {
            var combo = control as ComboBox;
            if (combo != null)
            {
                var point = form.PointToClient(combo.PointToScreen(Point.Empty));
                point.Offset(form.PointToScreen(Point.Empty).X - form.Left, form.PointToScreen(Point.Empty).Y - form.Top);
                using (var graphics = Graphics.FromImage(image))
                using (var background = new SolidBrush(combo.BackColor))
                using (var foreground = new SolidBrush(combo.ForeColor))
                using (var format = new StringFormat { LineAlignment = StringAlignment.Center, Trimming = StringTrimming.EllipsisCharacter, FormatFlags = StringFormatFlags.NoWrap })
                {
                    var bounds = new Rectangle(point.X + 2, point.Y + 2, Math.Max(0, combo.Width - 24), combo.Height - 4);
                    graphics.FillRectangle(background, bounds);
                    bounds.X += 4; bounds.Width -= 4;
                    graphics.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAliasGridFit;
                    graphics.DrawString(combo.Text, combo.Font, foreground, bounds, format);
                }
            }
            foreach (Control child in control.Controls) PaintPreviewChoices(child, image, form);
        }
    }

    sealed class LauncherForm : Form
    {
        readonly ComboBox language = new ComboBox(), resolution = new ComboBox(), scale = new ComboBox();
        readonly TextBox gameFolder = new TextBox();
        readonly Button browse = new Button(), play = new Button(), cancel = new Button(), logs = new Button();
        readonly Label status = new Label(); readonly ProgressBar progress = new ProgressBar();
        readonly LinkLabel runtimeHelp = new LinkLabel();
        readonly BackgroundWorker worker = new BackgroundWorker(); readonly Timer timer = new Timer();
        Process game; bool closeAfterWork;

        public LauncherForm()
        {
            Text = "ProSpi3 Launcher"; ClientSize = new Size(880, 620); MinimumSize = new Size(840, 660);
            StartPosition = FormStartPosition.CenterScreen; Font = new Font("Segoe UI", 10F);
            BackColor = Color.FromArgb(248, 249, 252); ForeColor = Color.FromArgb(24, 40, 63); AutoScaleMode = AutoScaleMode.Font; DoubleBuffered = true;
            Icon = Icon.ExtractAssociatedIcon(Assembly.GetExecutingAssembly().Location);
            var header = new BrandHeader();
            var footer = new Panel { Dock = DockStyle.Bottom, Height = 78, Padding = new Padding(26, 14, 26, 14), BackColor = Color.White };
            play.Text = "▶  PLAY"; play.Size = new Size(145, 44); play.Margin = new Padding(0);
            play.BackColor = Color.FromArgb(224, 177, 79); play.FlatStyle = FlatStyle.Flat; play.FlatAppearance.BorderSize = 0;
            play.Font = new Font(Font, FontStyle.Bold); play.Click += Play;
            cancel.Text = "Cancel setup"; cancel.Size = new Size(125, 44); cancel.Margin = new Padding(0, 0, 10, 0);
            cancel.Visible = false; cancel.Click += delegate { worker.CancelAsync(); status.Text = "Stopping setup..."; };
            logs.Text = "Open logs"; logs.Size = new Size(110, 38); logs.Location = new Point(26, 19);
            logs.Click += delegate { Directory.CreateDirectory(ReleaseFiles.Local); Process.Start(new ProcessStartInfo(ReleaseFiles.Local) { UseShellExecute = true }); };
            var actions = new FlowLayoutPanel { Dock = DockStyle.Right, Width = 290, FlowDirection = FlowDirection.RightToLeft, WrapContents = false, Margin = new Padding(0) };
            actions.Controls.AddRange(new Control[] { play, cancel }); footer.Controls.Add(actions); footer.Controls.Add(logs);
            runtimeHelp.Text = "Install required runtime"; runtimeHelp.AutoSize = true; runtimeHelp.Location = new Point(150, 30); runtimeHelp.Visible = false;
            runtimeHelp.LinkClicked += delegate { Process.Start(new ProcessStartInfo("https://aka.ms/vc14/vc_redist.x64.exe") { UseShellExecute = true }); };
            footer.Controls.Add(runtimeHelp);
            var body = new TableLayoutPanel { Dock = DockStyle.Fill, Padding = new Padding(30, 17, 30, 12), ColumnCount = 3, RowCount = 8 };
            body.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 145)); body.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100)); body.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 102));
            foreach (var height in new[] { 43, 43, 35, 43, 43, 41, 10, 55 }) body.RowStyles.Add(new RowStyle(SizeType.Absolute, height));
            AddLabel(body, "Language", 0); language.Items.AddRange(new object[] { "English", "Japanese / 日本語" }); AddCombo(body, language, 1, 0, 2);
            AddLabel(body, "Game folder", 1); gameFolder.AutoSize = false; gameFolder.Height = 31; gameFolder.BorderStyle = BorderStyle.FixedSingle;
            gameFolder.Dock = DockStyle.Top; gameFolder.Margin = new Padding(0, 3, 8, 0); body.Controls.Add(gameFolder, 1, 1);
            browse.Text = "Browse..."; browse.Dock = DockStyle.Top; browse.Height = 31; browse.Margin = new Padding(0, 3, 0, 0); browse.Click += Browse; body.Controls.Add(browse, 2, 1);
            var hint = new Label { Text = "Select the extracted folder containing default.xex.", ForeColor = Color.DimGray, AutoSize = true, Dock = DockStyle.Fill };
            body.Controls.Add(hint, 1, 2); body.SetColumnSpan(hint, 2);
            AddLabel(body, "Resolution", 3); resolution.Items.AddRange(new object[] { "720p", "1080p", "1440p", "2160p" }); AddCombo(body, resolution, 1, 3, 2);
            AddLabel(body, "Rendering scale", 4); scale.Items.AddRange(new object[] { "Native (recommended)", "2× (experimental)", "3× (experimental)" }); AddCombo(body, scale, 1, 4, 2);
            var saves = new Label { Text = "Original files stay unchanged. Saves are separate for each language.", ForeColor = Color.DimGray, AutoSize = true, Dock = DockStyle.Fill };
            body.Controls.Add(saves, 0, 5); body.SetColumnSpan(saves, 3);
            progress.Dock = DockStyle.Fill; progress.Margin = new Padding(0); body.Controls.Add(progress, 0, 6); body.SetColumnSpan(progress, 3);
            status.Text = "Choose your game folder, then select Play."; status.Dock = DockStyle.Fill; status.Margin = new Padding(0, 9, 0, 0); status.AutoEllipsis = true; status.UseMnemonic = false;
            body.Controls.Add(status, 0, 7); body.SetColumnSpan(status, 3);
            Controls.Add(body); Controls.Add(footer); Controls.Add(header); AcceptButton = play;
            foreach (var button in new[] { browse, logs, cancel }) { button.FlatStyle = FlatStyle.Flat; button.FlatAppearance.BorderColor = Color.FromArgb(204, 213, 224); button.BackColor = Color.White; }
            var settings = LoadSettings(); gameFolder.Text = settings.GameFolder; language.SelectedIndex = settings.Language == "Japanese" ? 1 : 0;
            resolution.SelectedItem = settings.Resolution; if (resolution.SelectedIndex < 0) resolution.SelectedIndex = 0;
            scale.SelectedIndex = Math.Max(0, Math.Min(2, settings.RenderScale - 1));
            worker.WorkerReportsProgress = true; worker.WorkerSupportsCancellation = true;
            worker.ProgressChanged += delegate(object sender, ProgressChangedEventArgs e) { progress.Value = Math.Max(0, Math.Min(100, e.ProgressPercentage)); status.Text = (string)e.UserState; };
            worker.DoWork += Prepare;
            worker.RunWorkerCompleted += Finished;
            timer.Interval = 1000; timer.Tick += delegate {
                if (game != null && game.HasExited) { bool failed = game.ExitCode != 0; game.Dispose(); game = null; timer.Stop(); SetBusy(false);
                    status.Text = failed ? "The game closed with an error. Open logs for details." : "The game has closed. Ready to play again."; }
            };
            FormClosing += delegate(object sender, FormClosingEventArgs e) { if (worker.IsBusy) { e.Cancel = true; closeAfterWork = true; worker.CancelAsync(); status.Text = "Stopping setup..."; } };
        }
        static void AddLabel(TableLayoutPanel panel, string text, int row)
        { panel.Controls.Add(new Label { Text = text, AutoSize = true, Margin = new Padding(0, 8, 5, 0) }, 0, row); }
        static void AddCombo(TableLayoutPanel panel, ComboBox combo, int column, int row, int span)
        { combo.DropDownStyle = ComboBoxStyle.DropDownList; combo.FlatStyle = FlatStyle.Flat; combo.BackColor = Color.FromArgb(237, 241, 247); combo.Dock = DockStyle.Top; combo.Margin = new Padding(0, 3, 0, 0); panel.Controls.Add(combo, column, row); panel.SetColumnSpan(combo, span); }
        Settings LoadSettings()
        {
            try { var file = Path.Combine(ReleaseFiles.Local, "launcher-settings.json"); if (File.Exists(file)) { var saved = ReleaseFiles.Json.Deserialize<Settings>(File.ReadAllText(file)); if (saved != null) return saved; } }
            catch (Exception) { }
            var result = new Settings(); var original = Path.Combine(ReleaseFiles.Root, "local", "disc");
            if (File.Exists(Path.Combine(original, "default.xex"))) result.GameFolder = original; return result;
        }
        void Browse(object sender, EventArgs e)
        {
            using (var dialog = new FolderBrowserDialog { Description = "Choose your extracted Japanese Xbox 360 game folder", ShowNewFolderButton = false })
            { if (Directory.Exists(gameFolder.Text)) dialog.SelectedPath = gameFolder.Text; if (dialog.ShowDialog(this) == DialogResult.OK) gameFolder.Text = dialog.SelectedPath; }
        }
        void SetBusy(bool busy)
        { play.Enabled = !busy; browse.Enabled = !busy; language.Enabled = !busy; resolution.Enabled = !busy; scale.Enabled = !busy; gameFolder.Enabled = !busy; cancel.Visible = worker.IsBusy; }
        void Play(object sender, EventArgs e)
        {
            if (String.IsNullOrWhiteSpace(gameFolder.Text)) { status.Text = "Choose your extracted game folder first."; return; }
            if (Process.GetProcessesByName("prospi3").Length != 0) { status.Text = "The game is already running. Close it before starting another session."; return; }
            var settings = new Settings { GameFolder = gameFolder.Text, Language = language.SelectedIndex == 1 ? "Japanese" : "English", Resolution = (string)resolution.SelectedItem, RenderScale = scale.SelectedIndex + 1 };
            ReleaseFiles.Log("Preparing " + settings.Language + ", " + settings.Resolution + ", rendering scale " + settings.RenderScale);
            SetBusy(true); cancel.Visible = true; progress.Value = 0; status.Text = "Checking game files..."; worker.RunWorkerAsync(settings);
        }
        void Prepare(object sender, DoWorkEventArgs e)
        {
            try
            {
                var settings = (Settings)e.Argument; Func<bool> cancelled = delegate { return worker.CancellationPending; };
                settings.GameFolder = ReleaseFiles.ValidateGame(settings.GameFolder, cancelled);
                var folder = settings.Language == "English" ? ReleaseFiles.PrepareEnglish(settings.GameFolder, delegate(int value, string text) { worker.ReportProgress(value, text); }, cancelled) : settings.GameFolder;
                if (cancelled()) throw new OperationCanceledException();
                var plan = ReleaseFiles.MakePlan(settings, folder); Directory.CreateDirectory(ReleaseFiles.Local);
                File.WriteAllText(Path.Combine(ReleaseFiles.Local, "launcher-settings.json"), ReleaseFiles.Json.Serialize(settings)); e.Result = plan;
            }
            catch (OperationCanceledException) { e.Cancel = true; }
        }
        void Finished(object sender, RunWorkerCompletedEventArgs e)
        {
            cancel.Visible = false;
            if (closeAfterWork) { Close(); return; }
            if (e.Cancelled) { SetBusy(false); progress.Value = 0; status.Text = "Setup cancelled. Original files are unchanged."; return; }
            if (e.Error != null) { ReleaseFiles.Log(e.Error.ToString()); SetBusy(false); progress.Value = 0; status.Text = e.Error.Message; return; }
            try { game = ReleaseFiles.StartGame((LaunchPlan)e.Result); progress.Value = 100; status.Text = "Game is running. Close it to change language or settings."; timer.Start(); }
            catch (Exception error) { ReleaseFiles.Log(error.ToString()); SetBusy(false); status.Text = error.Message; runtimeHelp.Visible = error is MissingRuntimeException; }
        }
    }
}
