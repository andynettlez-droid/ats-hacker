param(
  [string]$WorkDir = (Get-Location).Path,
  [string]$Out = "signal_pipeline_review.mp4",
  [string]$BackgroundClip = "",
  [switch]$BurnCaptions = $false
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $WorkDir

function Find-Tool([string]$Name) {
  $cmd = Get-Command $Name -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  $wingetRoot = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
  if (Test-Path -LiteralPath $wingetRoot) {
    $match = Get-ChildItem -Path $wingetRoot -Recurse -Filter "$Name.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($match) { return $match.FullName }
  }
  throw "$Name not found. Install ffmpeg/ffprobe first."
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

function Read-Caption([string]$Path, [string]$Fallback) {
  if (Test-Path -LiteralPath $Path) {
    $text = (Get-Content -LiteralPath $Path -Raw).Trim()
    if ($text) { return $text }
  }
  return $Fallback
}

function Split-Caption([string]$Text) {
  $words = $Text -replace "\s+", " " -split " "
  $chunks = New-Object System.Collections.Generic.List[string]
  $current = New-Object System.Collections.Generic.List[string]
  foreach ($word in $words) {
    if ($current.Count -ge 7) {
      $chunks.Add(($current -join " "))
      $current.Clear()
    }
    $current.Add($word)
  }
  if ($current.Count -gt 0) {
    $chunks.Add(($current -join " "))
  }
  return $chunks
}

function Write-Srt([object[]]$Segments, [string]$Path) {
  $cue = 1
  $lines = New-Object System.Collections.Generic.List[string]
  foreach ($segment in $Segments) {
    $chunks = Split-Caption $segment.Caption
    if ($chunks.Count -eq 0) { continue }
    $span = ($segment.End - $segment.Start) / $chunks.Count
    for ($i = 0; $i -lt $chunks.Count; $i++) {
      $start = $segment.Start + ($span * $i)
      $end = if ($i -eq $chunks.Count - 1) { $segment.End } else { $segment.Start + ($span * ($i + 1)) }
      $lines.Add([string]$cue)
      $lines.Add("$(Format-Timestamp $start) --> $(Format-Timestamp $end)")
      $lines.Add($chunks[$i])
      $lines.Add("")
      $cue += 1
    }
  }
  Set-Content -LiteralPath $Path -Value ($lines -join "`r`n") -Encoding UTF8
}

$ffmpeg = Find-Tool "ffmpeg"
$ffprobe = Find-Tool "ffprobe"

$Inputs = @(
  @{ Shot = "shot01.mp4"; Voice = "vo_hook.mp3"; Caption = Read-Caption "vo_hook.txt" "Let's look at this resume." },
  @{ Shot = "shot02.mp4"; Voice = "vo_search.mp3"; Caption = Read-Caption "vo_search.txt" "The recruiter search misses it." },
  @{ Shot = "shot03.mp4"; Voice = "vo_demo.mp3"; Caption = Read-Caption "vo_demo.txt" "Now rewrite the weak bullet." },
  @{ Shot = "shot04.mp4"; Voice = "vo_cta.mp3"; Caption = Read-Caption "vo_cta.txt" "Need yours fixed? Link in bio." }
)

foreach ($input in $Inputs) {
  foreach ($name in @($input.Shot, $input.Voice)) {
    if (-not (Test-Path -LiteralPath $name)) {
      throw "Missing input: $name"
    }
  }
}

if (Test-Path -LiteralPath $Out) {
  $backup = [IO.Path]::GetFileNameWithoutExtension($Out) + "_backup_" + (Get-Date -Format "yyyyMMddHHmmss") + [IO.Path]::GetExtension($Out)
  Copy-Item -LiteralPath $Out -Destination $backup -Force
}

$VideoFilter = "scale=1188:2112:force_original_aspect_ratio=increase,crop=1080:1920:(iw-ow)/2:(ih-oh)/2,fps=30,setsar=1,format=yuv420p"
$HandPlateFilter = "scale=1188:2112:force_original_aspect_ratio=increase,crop=1080:1920:(iw-ow)/2:(ih-oh)/2,fps=30,setsar=1,chromakey=0x00FF00:0.16:0.08,format=rgba"
$Segments = New-Object System.Collections.Generic.List[object]
$ConcatLines = New-Object System.Collections.Generic.List[string]
$timelineStart = 0.0

for ($i = 0; $i -lt $Inputs.Count; $i++) {
  $input = $Inputs[$i]
  $index = "{0:00}" -f ($i + 1)
  $segmentPath = "segment_$index.mp4"
  $overlayPath = "overlay$index.png"
  $overlayFrameDir = "overlay$index`_frames"
  $overlayFramePattern = Join-Path $overlayFrameDir "%04d.png"
  $handPlatePath = "handplate$index.mp4"
  $shotPath = if ($BackgroundClip) { $BackgroundClip } else { $input.Shot }
  $duration = Get-Duration $input.Voice
  $fadeOutStart = [math]::Max(0.0, $duration - 0.12)
  $audioFilter = "loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=in:st=0:d=0.04,afade=t=out:st=$('{0:F3}' -f $fadeOutStart):d=0.12"
  if ((Test-Path -LiteralPath $overlayFrameDir) -and (Test-Path -LiteralPath $handPlatePath)) {
    Invoke-FFmpeg @(
      "-y",
      "-stream_loop", "-1",
      "-i", $shotPath,
      "-i", $input.Voice,
      "-framerate", "30",
      "-i", $overlayFramePattern,
      "-stream_loop", "-1",
      "-i", $handPlatePath,
      "-t", ("{0:F3}" -f $duration),
      "-filter_complex", "[0:v]$VideoFilter[base];[base][2:v]overlay=0:0:format=auto[doc];[3:v]$HandPlateFilter[hand];[doc][hand]overlay=0:0:format=auto[v]",
      "-af", $audioFilter,
      "-map", "[v]",
      "-map", "1:a",
      "-c:v", "libx264",
      "-preset", "medium",
      "-crf", "18",
      "-pix_fmt", "yuv420p",
      "-c:a", "aac",
      "-ar", "48000",
      "-ac", "2",
      $segmentPath
    )
  } elseif (Test-Path -LiteralPath $overlayFrameDir) {
    Invoke-FFmpeg @(
      "-y",
      "-stream_loop", "-1",
      "-i", $shotPath,
      "-i", $input.Voice,
      "-framerate", "30",
      "-i", $overlayFramePattern,
      "-t", ("{0:F3}" -f $duration),
      "-filter_complex", "[0:v]$VideoFilter[base];[base][2:v]overlay=0:0:format=auto[v]",
      "-af", $audioFilter,
      "-map", "[v]",
      "-map", "1:a",
      "-c:v", "libx264",
      "-preset", "medium",
      "-crf", "18",
      "-pix_fmt", "yuv420p",
      "-c:a", "aac",
      "-ar", "48000",
      "-ac", "2",
      $segmentPath
    )
  } elseif ((Test-Path -LiteralPath $overlayPath) -and (Test-Path -LiteralPath $handPlatePath)) {
    Invoke-FFmpeg @(
      "-y",
      "-stream_loop", "-1",
      "-i", $shotPath,
      "-i", $input.Voice,
      "-i", $overlayPath,
      "-stream_loop", "-1",
      "-i", $handPlatePath,
      "-t", ("{0:F3}" -f $duration),
      "-filter_complex", "[0:v]$VideoFilter[base];[base][2:v]overlay=0:0:format=auto[doc];[3:v]$HandPlateFilter[hand];[doc][hand]overlay=0:0:format=auto[v]",
      "-af", $audioFilter,
      "-map", "[v]",
      "-map", "1:a",
      "-c:v", "libx264",
      "-preset", "medium",
      "-crf", "18",
      "-pix_fmt", "yuv420p",
      "-c:a", "aac",
      "-ar", "48000",
      "-ac", "2",
      $segmentPath
    )
  } elseif (Test-Path -LiteralPath $overlayPath) {
    Invoke-FFmpeg @(
      "-y",
      "-stream_loop", "-1",
      "-i", $shotPath,
      "-i", $input.Voice,
      "-i", $overlayPath,
      "-t", ("{0:F3}" -f $duration),
      "-filter_complex", "[0:v]$VideoFilter[base];[base][2:v]overlay=0:0:format=auto[v]",
      "-af", $audioFilter,
      "-map", "[v]",
      "-map", "1:a",
      "-c:v", "libx264",
      "-preset", "medium",
      "-crf", "18",
      "-pix_fmt", "yuv420p",
      "-c:a", "aac",
      "-ar", "48000",
      "-ac", "2",
      $segmentPath
    )
  } elseif (Test-Path -LiteralPath $handPlatePath) {
    Invoke-FFmpeg @(
      "-y",
      "-stream_loop", "-1",
      "-i", $shotPath,
      "-i", $input.Voice,
      "-stream_loop", "-1",
      "-i", $handPlatePath,
      "-t", ("{0:F3}" -f $duration),
      "-filter_complex", "[0:v]$VideoFilter[base];[2:v]$HandPlateFilter[hand];[base][hand]overlay=0:0:format=auto[v]",
      "-af", $audioFilter,
      "-map", "[v]",
      "-map", "1:a",
      "-c:v", "libx264",
      "-preset", "medium",
      "-crf", "18",
      "-pix_fmt", "yuv420p",
      "-c:a", "aac",
      "-ar", "48000",
      "-ac", "2",
      $segmentPath
    )
  } else {
    Invoke-FFmpeg @(
      "-y",
      "-stream_loop", "-1",
      "-i", $shotPath,
      "-i", $input.Voice,
      "-t", ("{0:F3}" -f $duration),
      "-vf", $VideoFilter,
      "-af", $audioFilter,
      "-map", "0:v",
      "-map", "1:a",
      "-c:v", "libx264",
      "-preset", "medium",
      "-crf", "18",
      "-pix_fmt", "yuv420p",
      "-c:a", "aac",
      "-ar", "48000",
      "-ac", "2",
      $segmentPath
    )
  }
  $ConcatLines.Add("file '$segmentPath'")
  $Segments.Add([pscustomobject]@{
    Start = $timelineStart
    End = $timelineStart + $duration
    Caption = $input.Caption
  })
  $timelineStart += $duration
}

Set-Content -LiteralPath "concat_list.txt" -Value ($ConcatLines -join "`n") -NoNewline
Invoke-FFmpeg @("-y", "-f", "concat", "-safe", "0", "-i", "concat_list.txt", "-c", "copy", "signal_pipeline_rough.mp4")

Write-Srt $Segments "signal_pipeline_captions.srt"
if ($BurnCaptions) {
  Invoke-FFmpeg @(
    "-y",
    "-i", "signal_pipeline_rough.mp4",
    "-vf", "subtitles=signal_pipeline_captions.srt:force_style='Fontsize=10,Bold=1,Alignment=2,MarginV=76,Outline=1,Shadow=0'",
    "-c:v", "libx264",
    "-preset", "medium",
    "-crf", "18",
    "-pix_fmt", "yuv420p",
    "-c:a", "copy",
    "-movflags", "+faststart",
    $Out
  )
} else {
  Invoke-FFmpeg @(
    "-y",
    "-i", "signal_pipeline_rough.mp4",
    "-c:v", "libx264",
    "-preset", "medium",
    "-crf", "18",
    "-pix_fmt", "yuv420p",
    "-c:a", "copy",
    "-movflags", "+faststart",
    $Out
  )
}

& $ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height,r_frame_rate -of default=nw=1 $Out
& $ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,sample_rate,channels -of default=nw=1 $Out
& $ffprobe -v error -show_entries format=duration,size -of default=nw=1 $Out
Write-Host "Done -> $((Resolve-Path -LiteralPath $Out).Path)"
