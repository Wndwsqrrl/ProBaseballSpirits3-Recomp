using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;
using System.Reflection;
using System.Windows.Forms;

namespace ProSpi3Launcher
{
    sealed class BrandHeader : Panel
    {
        readonly Image atlas;
        public BrandHeader()
        {
            Dock = DockStyle.Top; Height = 200; DoubleBuffered = true;
            using (var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream("ProSpi3.title-atlas.png"))
            {
                if (stream == null) throw new FileNotFoundException("The launcher title artwork is missing.");
                using (var image = Image.FromStream(stream)) atlas = (Image)image.Clone();
            }
        }
        protected override void OnPaint(PaintEventArgs e)
        {
            base.OnPaint(e); var g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias; g.InterpolationMode = InterpolationMode.HighQualityBicubic;
            using (var fill = new LinearGradientBrush(ClientRectangle, Color.FromArgb(22, 58, 103), Color.FromArgb(8, 21, 39), 15F)) g.FillRectangle(fill, ClientRectangle);
            using (var line = new Pen(Color.FromArgb(22, 181, 215, 249), 1.3F))
            {
                var x = Width - 85;
                g.DrawPolygon(line, new[] { new Point(x, 12), new Point(x + 94, 106), new Point(x, 200), new Point(x - 94, 106) });
                g.DrawPolygon(line, new[] { new Point(x, 43), new Point(x + 63, 106), new Point(x, 169), new Point(x - 63, 106) });
            }
            // Use the original atlas rectangle and alpha without redrawing the wordmark.
            g.DrawImage(atlas, new Rectangle(18, 7, 300, 182), new Rectangle(4, 4, 632, 384), GraphicsUnit.Pixel);
            using (var title = new Font("Segoe UI", 18F, FontStyle.Bold))
            using (var small = new Font("Segoe UI", 10F))
            using (var tag = new Font("Segoe UI", 10F, FontStyle.Bold))
            using (var gold = new SolidBrush(Color.FromArgb(239, 193, 96)))
            using (var muted = new SolidBrush(Color.FromArgb(184, 203, 224)))
            {
                g.DrawString("PRO YAKYUU SPIRITS 3", title, Brushes.White, 340, 34);
                g.DrawString("R E C O M P", tag, gold, 343, 76);
                g.DrawString("Play on Windows. Choose your language.", small, muted, 343, 109);
                using (var pill = new SolidBrush(Color.FromArgb(30, 53, 82))) g.FillRectangle(pill, 343, 145, 145, 28);
                g.DrawString("PREVIEW  /  0.1", small, gold, 353, 150);
            }
            using (var accent = new SolidBrush(Color.FromArgb(184, 43, 42))) g.FillRectangle(accent, 0, Height - 4, Width, 4);
        }
        protected override void Dispose(bool disposing) { if (disposing) atlas.Dispose(); base.Dispose(disposing); }
    }
}
