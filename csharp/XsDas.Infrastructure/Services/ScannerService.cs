using XsDas.Core.Interfaces;
using XsDas.Core.Utils;

namespace XsDas.Infrastructure.Services;

/// <summary>
/// Implementation of bridge scanner service.
/// Ports all 15 classic bridge algorithms from Python bridges_classic.py
/// </summary>
public class ScannerService : IScannerService
{
    private static readonly string[] DefaultResult = new[] { "00", "55" };

    public string[] ScanCau1StlP5(object[] row)
    {
        try
        {
            var gdb = (row[2]?.ToString() ?? "00000").Trim();
            var de = gdb.Length >= 2 ? gdb[^2..] : "00";
            de = de.PadLeft(2, '0');
            
            var a = int.Parse(de[0].ToString());
            var b = int.Parse(de[1].ToString());
            var x = (a + 5) % 10;
            var y = (b + 5) % 10;
            
            return LotteryUtils.TaoStlV30Bong(x, y);
        }
        catch
        {
            return DefaultResult;
        }
    }

    public string[] ScanCau2Vt1(object[] row)
    {
        try
        {
            var g6 = (row[8]?.ToString() ?? ",,").Split(',');
            var g7 = (row[9]?.ToString() ?? ",,,").Split(',');
            
            var a = g6.Length > 2 ? g6[2].Trim() : "0";
            a = a.Length > 0 ? a[^1..] : "0";
            
            var b = g7.Length > 3 ? g7[3].Trim() : "0";
            b = b.Length > 0 ? b[^1..] : "0";
            
            return LotteryUtils.TaoStlV30Bong(
                int.Parse(string.IsNullOrEmpty(a) ? "0" : a),
                int.Parse(string.IsNullOrEmpty(b) ? "0" : b)
            );
        }
        catch
        {
            return DefaultResult;
        }
    }

    public string[] ScanCau3Vt2(object[] row)
    {
        try
        {
            var a = (row[2]?.ToString() ?? "0").Trim();
            a = a.Length > 0 ? a[^1..] : "0";
            
            var b = (row[3]?.ToString() ?? "0").Trim();
            b = b.Length > 0 ? b[^1..] : "0";
            
            return LotteryUtils.TaoStlV30Bong(
                int.Parse(string.IsNullOrEmpty(a) ? "0" : a),
                int.Parse(string.IsNullOrEmpty(b) ? "0" : b)
            );
        }
        catch
        {
            return DefaultResult;
        }
    }

    public string[] ScanCau4Vt3(object[] row)
    {
        try
        {
            var gdb = (row[2]?.ToString() ?? "00000").Trim();
            var a = gdb.Length >= 2 ? gdb[^2..^1] : "0";
            
            var b = (row[3]?.ToString() ?? "0").Trim();
            b = b.Length > 0 ? b[^1..] : "0";
            
            return LotteryUtils.TaoStlV30Bong(
                int.Parse(string.IsNullOrEmpty(a) ? "0" : a),
                int.Parse(string.IsNullOrEmpty(b) ? "0" : b)
            );
        }
        catch
        {
            return DefaultResult;
        }
    }

    public string[] ScanCau5Tdb1(object[] row)
    {
        try
        {
            var g7 = (row[9]?.ToString() ?? ",,,").Split(',');
            
            var a = g7.Length > 0 && !string.IsNullOrEmpty(g7[0]) ? g7[0].Trim() : "0";
            a = a.Length > 0 ? a[..1] : "0";
            
            var b = g7.Length > 3 ? g7[3].Trim() : "0";
            b = b.Length > 0 ? b[^1..] : "0";
            
            return LotteryUtils.TaoStlV30Bong(
                int.Parse(string.IsNullOrEmpty(a) ? "0" : a),
                int.Parse(string.IsNullOrEmpty(b) ? "0" : b)
            );
        }
        catch
        {
            return DefaultResult;
        }
    }

    public string[] ScanCau6Vt5(object[] row)
    {
        try
        {
            var g7 = (row[9]?.ToString() ?? ",,,").Split(',');
            
            var a = g7.Length > 1 ? g7[1].Trim() : "0";
            a = a.Length > 0 ? a[^1..] : "0";
            
            var b = g7.Length > 2 ? g7[2].Trim() : "0";
            b = b.Length > 0 ? b[..1] : "0";
            
            return LotteryUtils.TaoStlV30Bong(
                int.Parse(string.IsNullOrEmpty(a) ? "0" : a),
                int.Parse(string.IsNullOrEmpty(b) ? "0" : b)
            );
        }
        catch
        {
            return DefaultResult;
        }
    }

    public string[] ScanCau7Moi1(object[] row)
    {
        try
        {
            var g5 = (row[7]?.ToString() ?? ",,,,,").Split(',');
            var g7 = (row[9]?.ToString() ?? ",,,").Split(',');
            
            var a = g5.Length > 0 && !string.IsNullOrEmpty(g5[0]) ? g5[0].Trim() : "0";
            a = a.Length > 0 ? a[..1] : "0";
            
            var b = g7.Length > 0 && !string.IsNullOrEmpty(g7[0]) ? g7[0].Trim() : "0";
            b = b.Length > 0 ? b[..1] : "0";
            
            return LotteryUtils.TaoStlV30Bong(
                int.Parse(string.IsNullOrEmpty(a) ? "0" : a),
                int.Parse(string.IsNullOrEmpty(b) ? "0" : b)
            );
        }
        catch
        {
            return DefaultResult;
        }
    }

    public string[] ScanCau8Moi2(object[] row)
    {
        try
        {
            var g3 = (row[5]?.ToString() ?? ",,,,,").Split(',');
            var g4 = (row[6]?.ToString() ?? ",,,").Split(',');
            
            var a = g3.Length > 0 && !string.IsNullOrEmpty(g3[0]) ? g3[0].Trim() : "0";
            a = a.Length > 0 ? a[..1] : "0";
            
            var b = g4.Length > 0 && !string.IsNullOrEmpty(g4[0]) ? g4[0].Trim() : "0";
            b = b.Length > 0 ? b[..1] : "0";
            
            return LotteryUtils.TaoStlV30Bong(
                int.Parse(string.IsNullOrEmpty(a) ? "0" : a),
                int.Parse(string.IsNullOrEmpty(b) ? "0" : b)
            );
        }
        catch
        {
            return DefaultResult;
        }
    }

    public string[] ScanCau9Moi3(object[] row)
    {
        try
        {
            var a = (row[2]?.ToString() ?? "0").Trim();
            a = a.Length > 0 ? a[..1] : "0";
            
            var b = (row[3]?.ToString() ?? "0").Trim();
            b = b.Length > 0 ? b[..1] : "0";
            
            return LotteryUtils.TaoStlV30Bong(
                int.Parse(string.IsNullOrEmpty(a) ? "0" : a),
                int.Parse(string.IsNullOrEmpty(b) ? "0" : b)
            );
        }
        catch
        {
            return DefaultResult;
        }
    }

    public string[] ScanCau10Moi4(object[] row)
    {
        try
        {
            var g2 = (row[4]?.ToString() ?? ",0").Split(',');
            var g3 = (row[5]?.ToString() ?? ",,0").Split(',');
            
            var aStr = g2.Length > 1 ? g2[1].Trim() : "00";
            var a = aStr.Length >= 2 ? aStr[1..2] : "0";
            
            var b = g3.Length > 2 ? g3[2].Trim() : "00000";
            b = b.Length > 0 ? b[^1..] : "0";
            
            return LotteryUtils.TaoStlV30Bong(
                int.Parse(string.IsNullOrEmpty(a) ? "0" : a),
                int.Parse(string.IsNullOrEmpty(b) ? "0" : b)
            );
        }
        catch
        {
            return DefaultResult;
        }
    }

    public string[] ScanCau11Moi5(object[] row)
    {
        try
        {
            var gdb = (row[2]?.ToString() ?? "00").Trim();
            var a = gdb.Length >= 2 ? gdb[1..2] : "0";
            
            var g3 = (row[5]?.ToString() ?? ",0").Split(',');
            var b = g3.Length > 1 ? g3[1].Trim() : "00000";
            b = b.Length > 0 ? b[^1..] : "0";
            
            return LotteryUtils.TaoStlV30Bong(
                int.Parse(string.IsNullOrEmpty(a) ? "0" : a),
                int.Parse(string.IsNullOrEmpty(b) ? "0" : b)
            );
        }
        catch
        {
            return DefaultResult;
        }
    }

    public string[] ScanCau12Moi6(object[] row)
    {
        try
        {
            var gdb = (row[2]?.ToString() ?? "00000").Trim();
            var a = gdb.Length > 0 ? gdb[^1..] : "0";
            
            var g3 = (row[5]?.ToString() ?? ",,0").Split(',');
            var bStr = g3.Length > 2 ? g3[2].Trim() : "000";
            var b = bStr.Length >= 3 ? bStr[2..3] : "0";
            
            return LotteryUtils.TaoStlV30Bong(
                int.Parse(string.IsNullOrEmpty(a) ? "0" : a),
                int.Parse(string.IsNullOrEmpty(b) ? "0" : b)
            );
        }
        catch
        {
            return DefaultResult;
        }
    }

    public string[] ScanCau13G7_3P8(object[] row)
    {
        try
        {
            var g7 = (row[9]?.ToString() ?? ",,0").Split(',');
            var baseNum = g7.Length > 2 ? g7[2].Trim() : "0";
            baseNum = baseNum.PadLeft(2, '0');
            
            var a = int.Parse(baseNum[0].ToString());
            var b = int.Parse(baseNum[1].ToString());
            var x = (a + 8) % 10;
            var y = (b + 8) % 10;
            
            return LotteryUtils.TaoStlV30Bong(x, y);
        }
        catch
        {
            return DefaultResult;
        }
    }

    public string[] ScanCau14G1P2(object[] row)
    {
        try
        {
            var g1 = (row[3]?.ToString() ?? "00").Trim();
            var baseNum = g1.Length >= 2 ? g1[^2..] : "00";
            baseNum = baseNum.PadLeft(2, '0');
            
            var a = int.Parse(baseNum[0].ToString());
            var b = int.Parse(baseNum[1].ToString());
            var x = (a + 2) % 10;
            var y = (b + 2) % 10;
            
            return LotteryUtils.TaoStlV30Bong(x, y);
        }
        catch
        {
            return DefaultResult;
        }
    }

    public string[] ScanCau15DeP7(object[] row)
    {
        try
        {
            var gdb = (row[2]?.ToString() ?? "00000").Trim();
            var baseNum = gdb.Length >= 2 ? gdb[^2..] : "00";
            baseNum = baseNum.PadLeft(2, '0');
            
            var a = int.Parse(baseNum[0].ToString());
            var b = int.Parse(baseNum[1].ToString());
            var x = (a + 7) % 10;
            var y = (b + 7) % 10;
            
            return LotteryUtils.TaoStlV30Bong(x, y);
        }
        catch
        {
            return DefaultResult;
        }
    }

    public IEnumerable<Func<object[], string[]>> GetAllBridgeScanners()
    {
        return new Func<object[], string[]>[]
        {
            ScanCau1StlP5,
            ScanCau2Vt1,
            ScanCau3Vt2,
            ScanCau4Vt3,
            ScanCau5Tdb1,
            ScanCau6Vt5,
            ScanCau7Moi1,
            ScanCau8Moi2,
            ScanCau9Moi3,
            ScanCau10Moi4,
            ScanCau11Moi5,
            ScanCau12Moi6,
            ScanCau13G7_3P8,
            ScanCau14G1P2,
            ScanCau15DeP7
        };
    }
}
