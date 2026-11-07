Add-Type -AssemblyName System.Drawing

function Generate-TerminalBitmap([int]$size) {
    $bmp = New-Object System.Drawing.Bitmap($size, $size, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
    $g.Clear([System.Drawing.Color]::Transparent)

    # Outer rounded rect / squircle
    $radius = [Math]::Max(2, [int]($size * 0.18))
    $d = $radius * 2

    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $path.AddArc(0, 0, $d, $d, 180, 90)
    $path.AddArc($size - $d, 0, $d, $d, 270, 90)
    $path.AddArc($size - $d, $size - $d, $d, $d, 0, 90)
    $path.AddArc(0, $size - $d, $d, $d, 90, 90)
    $path.CloseFigure()

    # Fill background: Dark charcoal / modern terminal background (#16161e)
    $brush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 22, 22, 30))
    $g.FillPath($brush, $path)

    # Accent outline: Modern cyan/blue (#38bdf8)
    $pen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(255, 56, 189, 248), [Math]::Max(1.0, $size * 0.035))
    $g.DrawPath($pen, $path)

    # Top traffic dots (only if size >= 32)
    if ($size -ge 32) {
        $dotRadius = [Math]::Max(2.0, $size * 0.035)
        $dotY = $size * 0.14
        $dotX1 = $size * 0.15
        $dotSpacing = $size * 0.09

        $redBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 244, 63, 94))
        $yelBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 250, 204, 21))
        $grnBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 34, 197, 94))

        $g.FillEllipse($redBrush, $dotX1, $dotY, $dotRadius * 2, $dotRadius * 2)
        $g.FillEllipse($yelBrush, $dotX1 + $dotSpacing, $dotY, $dotRadius * 2, $dotRadius * 2)
        $g.FillEllipse($grnBrush, $dotX1 + ($dotSpacing * 2), $dotY, $dotRadius * 2, $dotRadius * 2)
    }

    # Draw ">_" Terminal prompt symbol
    # Chevron ">" in vibrant cyan (#06b6d4)
    $fontSize = [Math]::Max(7.0, $size * 0.38)
    $fontFamily = "Consolas"
    $font = New-Object System.Drawing.Font($fontFamily, $fontSize, [System.Drawing.FontStyle]::Bold)

    $cyanBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 6, 182, 212))
    $greenBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 16, 185, 129))

    # Center prompt
    $yOffset = if ($size -ge 32) { $size * 0.30 } else { $size * 0.15 }
    $xOffset = $size * 0.14

    $g.DrawString(">", $font, $cyanBrush, $xOffset, $yOffset)

    # Cursor "_" or block
    $cursorX = $xOffset + ($size * 0.32)
    $g.DrawString("_", $font, $greenBrush, $cursorX, $yOffset)

    $g.Dispose()
    return $bmp
}

$assetsDir = Join-Path $PSScriptRoot "..\assets"
if (!(Test-Path $assetsDir)) { New-Item -ItemType Directory -Path $assetsDir -Force | Out-Null }

$bmp256 = Generate-TerminalBitmap 256
$pngPath = Join-Path $assetsDir "app.png"
$bmp256.Save($pngPath, [System.Drawing.Imaging.ImageFormat]::Png)

$icoPath = Join-Path $assetsDir "app.ico"
$icon = [System.Drawing.Icon]::FromHandle($bmp256.GetHicon())
$fs = [System.IO.FileStream]::new($icoPath, [System.IO.FileMode]::Create)
$icon.Save($fs)
$fs.Close()
$icon.Dispose()
$bmp256.Dispose()

Write-Host "Generated $pngPath and $icoPath successfully."
