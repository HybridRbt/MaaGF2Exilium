$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
Add-Type -AssemblyName System.Windows.Forms
$copiedFolder = $null
function Invoke-CopyPatch {
    param([string]$PythonPath, [string]$PatchPath, [string]$Mode)
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName = $PythonPath
    $info.Arguments = '"' + $PatchPath + '" ' + $Mode
    $info.WorkingDirectory = [System.IO.Path]::GetDirectoryName([System.IO.Path]::GetDirectoryName($PatchPath))
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $info.StandardOutputEncoding = [System.Text.Encoding]::UTF8
    $info.StandardErrorEncoding = [System.Text.Encoding]::UTF8
    $info.EnvironmentVariables['PYTHONUTF8'] = '1'
    $info.EnvironmentVariables['PYTHONIOENCODING'] = 'utf-8'
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $info
    try {
        if (-not $process.Start()) { throw '未能启动副本中的内置 Python。' }
        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()
        $process.WaitForExit()
        $output = $stdoutTask.Result + $stderrTask.Result
        $logPath = Join-Path ([System.IO.Path]::GetDirectoryName($PatchPath)) ($Mode + '-output.log')
        Set-Content -LiteralPath $logPath -Value $output -Encoding UTF8
        Write-Host $output
        if ($process.ExitCode -ne 0) {
            throw ("副本补丁操作失败：" + $Mode + "`r`n" + $output.Trim() + "`r`n完整日志：" + $logPath)
        }
    } finally { $process.Dispose() }
}
try {
    $picker = New-Object System.Windows.Forms.OpenFileDialog
    $picker.Title = '选择原助手程序（请先完全退出助手）'
    $picker.Filter = '少前2助手|MaaGF2Exilium.exe;MFAAvalonia.exe|可执行文件|*.exe'
    $picker.CheckFileExists = $true
    if ($picker.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { exit 0 }
    $sourceExe = [System.IO.Path]::GetFullPath($picker.FileName)
    $exeName = [System.IO.Path]::GetFileName($sourceExe)
    if ($exeName -notin @('MaaGF2Exilium.exe', 'MFAAvalonia.exe')) {
        throw '请选择 MaaGF2Exilium.exe 或 MFAAvalonia.exe，不能选择游戏或其他程序。'
    }
    $sourceFolder = [System.IO.Path]::GetDirectoryName($sourceExe)
    $sourceParent = [System.IO.Directory]::GetParent($sourceFolder)
    if ($null -eq $sourceParent) { throw '不支持助手直接安装在盘符根目录，请先移到独立文件夹。' }
    $interfacePath = Join-Path $sourceFolder 'interface.json'
    $pythonPath = Join-Path $sourceFolder 'python\python.exe'
    if (-not (Test-Path -LiteralPath $interfacePath -PathType Leaf) -or
        -not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
        throw '该目录缺少 interface.json 或 python\python.exe，请选择完整助手安装目录中的程序。'
    }
    $interface = Get-Content -LiteralPath $interfacePath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($interface.version -ne 'v2.7.2') {
        throw ('此包仅支持资源 v2.7.2；所选目录为 ' + $interface.version)
    }
    $running = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
        try { $_.Path -eq $sourceExe } catch { $false }
    })
    if ($running.Count -gt 0) { throw '原助手仍在运行。请等待任务结束并完全退出助手，再运行安装器；原程序没有被停止或修改。' }
    $payload = Join-Path $PSScriptRoot 'dialog-patch'
    if (-not (Test-Path -LiteralPath (Join-Path $payload 'manifest.json') -PathType Leaf)) {
        throw '安装包不完整，请解压整个压缩包后运行。'
    }
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $suffix = [Guid]::NewGuid().ToString('N').Substring(0, 6)
    $destinationName = [System.IO.Path]::GetFileName($sourceFolder) + '-补丁测试-' + $stamp + '-' + $suffix
    $copiedFolder = Join-Path $sourceParent.FullName $destinationName
    if (Test-Path -LiteralPath $copiedFolder) { throw '副本目标目录已存在，停止以免覆盖。' }
    Write-Host ('复制助手到: ' + $copiedFolder)
    Copy-Item -LiteralPath $sourceFolder -Destination $copiedFolder -Recurse -Force
    $copyPackage = Join-Path $copiedFolder 'dialog-patch'
    # Replace only the patch payload within the new copy, never the source folder.
    if (Test-Path -LiteralPath $copyPackage) { Remove-Item -LiteralPath $copyPackage -Recurse -Force }
    Copy-Item -LiteralPath $payload -Destination $copyPackage -Recurse -Force
    $copyPython = Join-Path $copiedFolder 'python\python.exe'
    $copyPatch = Join-Path $copyPackage 'patch.py'
    Push-Location -LiteralPath $copiedFolder
    try {
        if (Test-Path -LiteralPath (Join-Path $copiedFolder '.dialog-patch-backup')) {
            Write-Host '副本含旧测试补丁，先在副本中回滚。'
            Invoke-CopyPatch -PythonPath $copyPython -PatchPath $copyPatch -Mode rollback
        }
        Invoke-CopyPatch -PythonPath $copyPython -PatchPath $copyPatch -Mode apply
    } finally { Pop-Location }
    $copyExe = Join-Path $copiedFolder $exeName
    $desktop = [Environment]::GetFolderPath([Environment+SpecialFolder]::DesktopDirectory)
    if (-not (Test-Path -LiteralPath $desktop -PathType Container)) { throw '未能找到当前用户桌面，副本已打补丁，但快捷方式未创建。' }
    $shortcutPath = Join-Path $desktop ('少前2助手-补丁测试-' + $stamp + '-' + $suffix + '.lnk')
    if (Test-Path -LiteralPath $shortcutPath) { throw '同名桌面快捷方式已存在，未覆盖。' }
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $copyExe
    $shortcut.WorkingDirectory = $copiedFolder
    $shortcut.IconLocation = $copyExe + ',0'
    $shortcut.Description = '独立副本：极限峰值缺员确认、预演介绍关闭及多角色连续预演测试'
    $shortcut.Save()
    # Shell Link Header: RunAsUser (0x00002000) requests elevation at launch.
    $linkBytes = [System.IO.File]::ReadAllBytes($shortcutPath)
    if ($linkBytes.Length -lt 76 -or [BitConverter]::ToUInt32($linkBytes, 0) -ne 76) {
        throw '快捷方式头部格式异常，无法设置管理员启动。'
    }
    $linkBytes[21] = $linkBytes[21] -bor 32
    [System.IO.File]::WriteAllBytes($shortcutPath, $linkBytes)
    if ((([System.IO.File]::ReadAllBytes($shortcutPath))[21] -band 32) -eq 0) {
        throw '快捷方式管理员启动标志验证失败。'
    }
    $check = $shell.CreateShortcut($shortcutPath)
    if ($check.TargetPath -ne $copyExe -or $check.WorkingDirectory -ne $copiedFolder) {
        throw '快捷方式指向校验失败，请保留副本并反馈。'
    }
    $message = "已复制目录并在副本安装补丁。原文件夹未修改。`r`n`r`n副本：$copiedFolder`r`n桌面快捷方式：$shortcutPath`r`n`r`n尚未自动启动程序或运行游戏。请用新快捷方式启动；极限峰值缺员继续选项默认仍为 NO，测试时改为 YES。"
    Write-Host $message
    [System.Windows.Forms.MessageBox]::Show($message, '补丁副本安装完成') | Out-Null
} catch {
    $message = $_.Exception.Message
    if ($null -ne $copiedFolder) { $message += "`r`n副本路径：$copiedFolder" }
    $message += "`r`n原助手目录未被打补丁。"
    Write-Host $message -ForegroundColor Red
    [System.Windows.Forms.MessageBox]::Show($message, '安装未完成', [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error) | Out-Null
    exit 1
}
