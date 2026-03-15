# Requires -Version 5.1

# -------------------------------------------------------------------------
# 注意: 此脚本使用参数，允许您通过命令行直接传入 JAR 路径，
# 无需为每次比较编辑脚本文件。
# -------------------------------------------------------------------------

# =========================================================
# 1. 脚本参数 (允许通过命令行直接传入值)
# =========================================================

param(
    [Parameter(Mandatory=$true, HelpMessage="左侧 (旧) JAR 文件的完整路径。")]
    [string]$LeftJarPath, 
    
    [Parameter(Mandatory=$true, HelpMessage="右侧 (新) JAR 文件的完整路径。")]
    [string]$RightJarPath,
    
    [Parameter(Mandatory=$true, HelpMessage="包含要提取文件列表的文本文件路径。")]
    [string]$FileListPath,
    
    [Parameter(HelpMessage="目标输出目录。默认为 C:\Temp\ExtractedDiffs。")]
    [string]$TargetOutputDir = "C:\Temp\ExtractedDiffs",

    [Parameter(HelpMessage="Java 反编译器 JAR 文件的完整路径 (例如: C:\Tools\cfr-0.152.jar)。如果未提供，则跳过反编译步骤。")]
    [string]$DecompilerPath = "C:\Tools\cfr-0.152.jar"
)

# 此 PowerShell 脚本用于根据文件列表，从两个不同的 JAR 文件中批量提取指定文件，并可选择将 .class 文件内容替换为源代码。

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# =========================================================
# 2. 脚本设置与流程检查
# (使用上方定义的参数)
# =========================================================

# 检查必要输入文件是否存在
if (-not (Test-Path $FileListPath)) {
    Write-Error "错误: 找不到文件列表 $FileListPath 。请创建该文件并粘贴要提取的相对路径。"
    exit 1
}
if (-not (Test-Path $LeftJarPath)) {
    Write-Error "错误: 找不到左侧 (旧) JAR 文件 $LeftJarPath 。请检查路径。"
    exit 1
}
if (-not (Test-Path $RightJarPath)) {
    Write-Error "错误: 找不到右侧 (新) JAR 文件 $RightJarPath 。请检查路径。"
    exit 1
}

# 检查反编译器路径是否有效（如果提供了的话）
if (-not [string]::IsNullOrEmpty($DecompilerPath) -and -not (Test-Path $DecompilerPath)) {
    Write-Error "错误: 找不到反编译器 JAR 文件 $DecompilerPath 。请检查路径。"
    exit 1
}

# 创建目标输出目录
if (-not (Test-Path $TargetOutputDir)) {
    Write-Host "正在创建目标目录: $TargetOutputDir"
    New-Item -Path $TargetOutputDir -ItemType Directory | Out-Null
}

# 定义输出子目录路径
$V1OutputDir = Join-Path $TargetOutputDir "V1_$(Split-Path $LeftJarPath -Leaf)"
$V2OutputDir = Join-Path $TargetOutputDir "V2_$(Split-Path $RightJarPath -Leaf)"

# 确保两个版本的输出目录干净，并重新创建
Write-Host "正在清理和创建 V1/V2 输出目录..."
Remove-Item -Path $V1OutputDir -Recurse -Force -ErrorAction SilentlyContinue | Out-Null
Remove-Item -Path $V2OutputDir -Recurse -Force -ErrorAction SilentlyContinue | Out-Null
New-Item -Path $V1OutputDir -ItemType Directory | Out-Null
New-Item -Path $V2OutputDir -ItemType Directory | Out-Null

Write-Host "--- JAR 文件差异提取与内容替换工具 ---"
Write-Host "正在读取文件列表: $FileListPath"

# 初始化数组来记录提取成功的文件绝对路径
[Array]$V1ExtractedFiles = @()
[Array]$V2ExtractedFiles = @()

# 读取要提取的文件路径，并过滤空行和注释
$FilePaths = Get-Content $FileListPath | Where-Object { $_ -ne "" -and $_ -notmatch '^\s*#' }

if ($FilePaths.Count -eq 0) {
    Write-Host "文件列表为空。操作结束。"
    exit 0
}

# =========================================================
# 3. 核心功能：定义提取函数 Extract-JarEntry
# =========================================================

function Extract-JarEntry {
    param(
        [Parameter(Mandatory=$true)]
        [string]$ZipFilePath, # 输入的 JAR 文件路径
        [Parameter(Mandatory=$true)]
        [string]$EntryPath,   # JAR 内部的相对路径
        [Parameter(Mandatory=$true)]
        [string]$OutputBaseDir # 提取到的文件保存的基目录
    )

    # 引用 .NET 命名空间来操作 ZIP 文件（如果尚未加载）
    Add-Type -AssemblyName System.IO.Compression.FileSystem

    $ZipArchive = $null
    try {
        # 使用 ZipFile 打开 JAR (ZIP) 文件进行读取
        $ZipArchive = [System.IO.Compression.ZipFile]::OpenRead($ZipFilePath)

        # 查找条目。注意：JAR/ZIP 内部路径分隔符始终是斜杠 (/)
        $ZipEntryPath = $EntryPath.Replace("\", "/")
        $Entry = $ZipArchive.Entries | Where-Object { $_.FullName -eq $ZipEntryPath } | Select-Object -First 1

        if ($null -ne $Entry) {
            # 构造目标文件的完整路径
            $DestinationPath = Join-Path $OutputBaseDir $EntryPath
            
            # 确保目标文件的父目录存在
            $DestinationDir = Split-Path $DestinationPath -Parent
            if (-not (Test-Path $DestinationDir)) {
                New-Item -Path $DestinationDir -ItemType Directory | Out-Null
            }

            # 提取文件。$true 允许覆盖现有文件
            [System.IO.Compression.ZipFileExtensions]::ExtractToFile($Entry, $DestinationPath, $true) | Out-Null
            Write-Host "  ✅ 提取成功: $EntryPath" -ForegroundColor Green
            # 成功后返回文件的绝对路径
            return $DestinationPath
        } else {
            Write-Warning "  ⚠️ 警告: 文件 $EntryPath 在 $(Split-Path $ZipFilePath -Leaf) 中找不到。跳过。"
            # 返回空值
            return $null
        }
    }
    catch {
        Write-Error "提取 $EntryPath 时发生错误: $($_.Exception.Message)"
    }
    finally {
        # 确保无论发生什么，ZIP 存档都会被关闭和释放
        if ($null -ne $ZipArchive) {
            $ZipArchive.Dispose()
        }
    }
} # 确保函数闭合


# =========================================================
# 3.5. 辅助功能：执行反编译并替换文件内容 (已修复，直接捕获 STDOUT)
# =========================================================
# 将 .class 文件反编译成 .java 源代码，然后用源代码内容覆盖原 .class 文件。
function Invoke-JarDecompiler {
    param(
        [Parameter(Mandatory=$true)]
        [string]$ClassPath, # 要被覆盖的 .class 文件的绝对路径
        [Parameter(Mandatory=$true)]
        [string]$DecompilerPath # CFR.jar 等反编译器 JAR 路径
    )
    
    try {
        # 构建 Java 命令参数
        # --------------------------------------------------------------------------
        # 针对 CFR 反编译器修改: 移除反编译器自身的注释和版本信息。
        # 如果您使用的是其他反编译器，请替换为相应的 "禁止注释" 参数。
        # --------------------------------------------------------------------------
        $Arguments = @(
            "-jar",
            $DecompilerPath,
            "--comments", "false",       # 移除 CFR 自己的注释
            "--showversion", "false",    # 移除 CFR 的版本信息
            $ClassPath # 输入是原始的 .class 文件
        )

        # 执行 Java 命令。2>$null 抑制反编译器的日志/错误输出（如 "Processing..."），只捕获源代码（STDOUT）。
        $SourceCodeContent = & java $Arguments 2>$null | Out-String 
        
        # 检查是否捕获到内容 (假设源代码长度大于 100 字符)
        if (-not [string]::IsNullOrEmpty($SourceCodeContent) -and $SourceCodeContent.Length -gt 100) {
            
            # **关键步骤：** 用 Set-Content 替换 Out-File，以解决兼容性问题，并用源代码内容覆盖原有的 .class 文件
            Set-Content -Path $ClassPath -Value $SourceCodeContent -Encoding UTF8 -Force
            
            Write-Host "  📝 .class 文件内容已成功替换为源代码。 " -ForegroundColor Cyan

            return $true # 成功
        } else {
            # 如果没有捕获到足够的源代码内容，则认为失败
            Write-Error "反编译失败：未捕获到足够的源代码。请检查 Decompiler ($DecompilerPath) 是否能处理 $ClassPath。"
            return $false
        }
    }
    catch {
        # 捕获 Java 执行或 Set-Content 写入时的最终错误
        Write-Error "执行 Java 反编译命令或写入文件时发生错误: $($_.Exception.Message)"
        return $false
    }
}


# =========================================================
# 4. 循环执行提取过程 (新增反编译逻辑)
# =========================================================

foreach ($File in $FilePaths) {
    Write-Host "`n============================================="
    Write-Host "正在处理文件: $File"
    Write-Host "============================================="
    
    # 提取 V1 (旧版本) 文件，并记录路径
    Write-Host "-> 正在从 V1 文件 [$(Split-Path $LeftJarPath -Leaf)] 中提取..."
    $V1ExtractedPath = Extract-JarEntry -ZipFilePath $LeftJarPath -EntryPath $File -OutputBaseDir $V1OutputDir
    
    # 提取 V2 (新版本) 文件，并记录路径
    Write-Host "-> 正在从 V2 文件 [$(Split-Path $RightJarPath -Leaf)] 中提取..."
    $V2ExtractedPath = Extract-JarEntry -ZipFilePath $RightJarPath -EntryPath $File -OutputBaseDir $V2OutputDir
    
    # --- 新增反编译和替换逻辑 ---
    if ($File -like "*.class" -and -not [string]::IsNullOrEmpty($DecompilerPath)) {
        
        Write-Host "-> 正在尝试反编译 .class 文件并替换内容 ..." -ForegroundColor Yellow
        
        # 反编译并替换 V1
        if ($V1ExtractedPath) {
            # 移除不再需要的 -OutputBaseDir 参数
            $DecompileSuccess = Invoke-JarDecompiler -ClassPath $V1ExtractedPath -DecompilerPath $DecompilerPath
            if ($DecompileSuccess) {
                Write-Host "  ✅ V1 内容替换成功：文件 $File 现包含源代码。" -ForegroundColor Cyan
            }
        }
        
        # 反编译并替换 V2
        if ($V2ExtractedPath) {
            # 移除不再需要的 -OutputBaseDir 参数
            $DecompileSuccess = Invoke-JarDecompiler -ClassPath $V2ExtractedPath -DecompilerPath $DecompilerPath
            if ($DecompileSuccess) {
                Write-Host "  ✅ V2 内容替换成功：文件 $File 现包含源代码。" -ForegroundColor Cyan
            }
        }
    } elseif ($File -like "*.class" -and [string]::IsNullOrEmpty($DecompilerPath)) {
         Write-Host "-> 跳过 .class 文件的反编译。未提供 -DecompilerPath 参数。" -ForegroundColor DarkYellow
    }

    # 记录最终路径
    $V1ExtractedFiles += $V1ExtractedPath
    $V2ExtractedFiles += $V2ExtractedPath
}

# =========================================================
# 5. 结果总结 (路径文件输出)
# =========================================================

# -----------------------------------------------------
# 路径列表输出
# -----------------------------------------------------

$PathSummaryFile = Join-Path $TargetOutputDir "Extracted_File_Paths_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"

"==========================================================" | Out-File $PathSummaryFile -Encoding UTF8
"      JAR 差异提取与内容替换结果 - 文件路径列表" | Out-File $PathSummaryFile -Append -Encoding UTF8
"      运行时间: $(Get-Date)" | Out-File $PathSummaryFile -Append -Encoding UTF8
"==========================================================" | Out-File $PathSummaryFile -Append -Encoding UTF8

"`n--- 旧版本 (V1): $(Split-Path $LeftJarPath -Leaf) 文件路径 ---" | Out-File $PathSummaryFile -Append -Encoding UTF8
$V1ExtractedFiles | Where-Object { $_ -ne $null } | Out-File $PathSummaryFile -Append -Encoding UTF8

"`n--- 新版本 (V2): $(Split-Path $RightJarPath -Leaf) 文件路径 ---" | Out-File $PathSummaryFile -Append -Encoding UTF8
$V2ExtractedFiles | Where-Object { $_ -ne $null } | Out-File $PathSummaryFile -Append -Encoding UTF8

Write-Host "`n-----------------------------------------------------" -ForegroundColor DarkCyan
Write-Host "📁 提取文件的绝对路径已记录到以下文件：" -ForegroundColor Cyan
Write-Host "   $PathSummaryFile" -ForegroundColor Yellow
Write-Host "-----------------------------------------------------" -ForegroundColor DarkCyan
    
Write-Host "🎉 提取完成！所有指定的文件已成功提取到以下目录：" -ForegroundColor Green
Write-Host "旧版本 (V1) 输出目录: $V1OutputDir" -ForegroundColor Yellow
Write-Host "新版本 (V2) 输出目录: $V2OutputDir" -ForegroundColor Yellow
Write-Host "-----------------------------------------------------" -ForegroundColor DarkCyan

# 提示用户下一步操作
Write-Host "`n您可以将这两个目录导入到文件对比工具 (如 Beyond Compare, WinMerge) 中进行差异分析。请注意，.class 文件现在包含人类可读的源代码文本。"