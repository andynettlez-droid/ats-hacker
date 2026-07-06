param(
  [string]$WorkDir = (Get-Location).Path,
  [string]$Hook = "Woman_talking_about_resume_keywords_202607060959.mp4",
  [string]$Search = "Resume_cards_in_dark_void_202607060958.mp4",
  [string]$DemoImage = "signal_landing_demo.png",
  [string]$Cta = "Woman_speaking_to_camera_202607060956.mp4",
  [string]$VO1 = "ElevenLabs_2026-07-06T15_01_46_Abby_ivc_sp100_s50_sb75_se0_b_m2.mp3",
  [string]$VO2 = "ElevenLabs_2026-07-06T14_58_04_Abby_ivc_sp100_s50_sb75_se0_b_m2.mp3",
  [string]$Out = "signal_ad_final.mp4",
  [string]$Caption1 = 'The viral "ATS hack" is a myth',
  [string]$Caption2 = "Recruiters SEARCH. You're not ranking.",
  [string]$Caption3 = "Resume Crime Scene: 34 to 92",
  [string]$Caption4 = "Free score in bio - $9.99, no subscription"
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $WorkDir

function Find-Tool([string]$Name) {
  $cmd = Get-Command $Name -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  $winget = Get-ChildItem -Path "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Recurse -Filter "$Name.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($winget) { return $winget.FullName }
  throw "$Name not found. Install ffmpeg/ffprobe first."
}

$ffmpeg = Find-Tool "ffmpeg"
$ffprobe = Find-Tool "ffprobe"

foreach ($file in @($Hook, $Search, $DemoImage, $Cta, $VO1, $VO2)) {
  if (-not (Test-Path -LiteralPath $file)) {
    throw "Missing input: $file"
  }
}

function Invoke-FFmpeg([string[]]$ArgsList) {
  & $ffmpeg @ArgsList
  if ($LASTEXITCODE -ne 0) {
    throw "ffmpeg failed: $($ArgsList -join ' ')"
  }
}

function Get-Duration([string]$Path) {
  [double](& $ffprobe -v error -show_entries format=duration -of csv=p=0 $Path)
}

function Format-Timestamp([double]$Seconds) {
  $ms = [int][math]::Round($Seconds * 1000)
  $hh = [math]::Floor($ms / 3600000)
  $mm = [math]::Floor(($ms % 3600000) / 60000)
  $ss = [math]::Floor(($ms % 60000) / 1000)
  $mmm = $ms % 1000
  "{0:00}:{1:00}:{2:00},{3:000}" -f $hh, $mm, $ss, $mmm
}

if (Test-Path -LiteralPath $Out) {
  $backup = [IO.Path]::GetFileNameWithoutExtension($Out) + "_backup_" + (Get-Date -Format "yyyyMMddHHmmss") + [IO.Path]::GetExtension($Out)
  Copy-Item -LiteralPath $Out -Destination $backup -Force
}

$DHook = Get-Duration $Hook
$DCta = Get-Duration $Cta
$DVO1 = Get-Duration $VO1
$DVO2 = Get-Duration $VO2
$DemoFrames = [int][math]::Ceiling($DVO2 * 30)

$VF = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1"
$DemoVF = "fps=30,scale=1215:2160,crop=1080:1920:(iw-ow)/2:min(220\,n*220/$DemoFrames),setsar=1"

Invoke-FFmpeg @("-y", "-i", $Hook, "-vf", $VF, "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", "-ac", "2", "s1.mp4")
Invoke-FFmpeg @("-y", "-stream_loop", "-1", "-i", $Search, "-i", $VO1, "-t", ("{0:F3}" -f $DVO1), "-vf", $VF, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", "-ac", "2", "s2.mp4")
Invoke-FFmpeg @("-y", "-loop", "1", "-i", $DemoImage, "-i", $VO2, "-t", ("{0:F3}" -f $DVO2), "-vf", $DemoVF, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", "-ac", "2", "s3.mp4")
Invoke-FFmpeg @("-y", "-i", $Cta, "-vf", $VF, "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", "-ac", "2", "s4.mp4")

Set-Content -LiteralPath "list.txt" -Value "file 's1.mp4'`nfile 's2.mp4'`nfile 's3.mp4'`nfile 's4.mp4'`n" -NoNewline
Invoke-FFmpeg @("-y", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", "signal_ad_rough.mp4")

$T0 = 0.0
$T1 = $DHook
$T2 = $DHook + $DVO1
$T3 = $DHook + $DVO1 + $DVO2
$T4 = $DHook + $DVO1 + $DVO2 + $DCta

$Srt = @(
  "1", "$(Format-Timestamp $T0) --> $(Format-Timestamp $T1)", $Caption1, "",
  "2", "$(Format-Timestamp $T1) --> $(Format-Timestamp $T2)", $Caption2, "",
  "3", "$(Format-Timestamp $T2) --> $(Format-Timestamp $T3)", $Caption3, "",
  "4", "$(Format-Timestamp $T3) --> $(Format-Timestamp $T4)", $Caption4, ""
) -join "`r`n"
Set-Content -LiteralPath "signal_captions.srt" -Value $Srt -Encoding UTF8

Invoke-FFmpeg @("-y", "-i", "signal_ad_rough.mp4", "-vf", "subtitles=signal_captions.srt:force_style='Fontsize=16,Bold=1,Alignment=2,MarginV=90,Outline=2,Shadow=1'", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", $Out)

& $ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height,r_frame_rate -of default=nw=1 $Out
& $ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,sample_rate,channels -of default=nw=1 $Out
& $ffprobe -v error -show_entries format=duration,size -of default=nw=1 $Out
Write-Host "Done -> $((Resolve-Path -LiteralPath $Out).Path)"
