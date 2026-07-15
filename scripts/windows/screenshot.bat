REM Take a screenshot and save it
REM Usage: screenshot.bat [output_path]
REM Example: screenshot.bat screenshot.png

@echo off
set OUTPUT=%~1
if "%OUTPUT%"=="" (
    set OUTPUT=screenshot.png
)

powershell -Command "
Add-Type -AssemblyName System.Windows.Forms;
Add-Type -AssemblyName System.Drawing;
$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds;
$bitmap = New-Object System.Drawing.Bitmap($screen.Width, $screen.Height);
$graphics = [System.Drawing.Graphics]::FromImage($bitmap);
$graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size);
$bitmap.Save('%OUTPUT%');
$graphics.Dispose();
$bitmap.Dispose();
Write-Host 'Screenshot saved: %OUTPUT%';
"
