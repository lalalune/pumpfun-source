using System;
using System.Diagnostics;
using System.Text;
using System.Threading;
class LinkBridge {
  static string Quote(string value) {
    var b = new StringBuilder("\""); int slashes = 0;
    foreach (char c in value) {
      if (c == '\\') { slashes++; continue; }
      if (c == '"') { b.Append('\\', slashes * 2 + 1); b.Append(c); }
      else { b.Append('\\', slashes); b.Append(c); }
      slashes = 0;
    }
    b.Append('\\', slashes * 2); b.Append('"'); return b.ToString();
  }
  static int Main(string[] args) {
    string python = Environment.GetEnvironmentVariable("PUMP_PYTHON");
    string wrapper = Environment.GetEnvironmentVariable("PUMP_LINK_WRAPPER");
    if (String.IsNullOrEmpty(python) || String.IsNullOrEmpty(wrapper)) return 98;
    var command = new StringBuilder(Quote(wrapper));
    foreach (string arg in args) command.Append(" ").Append(Quote(arg));
    var info = new ProcessStartInfo(python, command.ToString());
    info.UseShellExecute = false; info.CreateNoWindow = true;
    info.RedirectStandardOutput = true; info.RedirectStandardError = true;
    using (var process = Process.Start(info)) {
      var stdout = new Thread(() => process.StandardOutput.BaseStream.CopyTo(Console.OpenStandardOutput()));
      var stderr = new Thread(() => process.StandardError.BaseStream.CopyTo(Console.OpenStandardError()));
      stdout.Start(); stderr.Start(); process.WaitForExit(); stdout.Join(); stderr.Join();
      return process.ExitCode;
    }
  }
}
