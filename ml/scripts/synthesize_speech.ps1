# Synthesises spoken audio for the held-out TEST utterances using the Windows built-in
# TTS voices (System.Speech). Output: ml/eval_audio/*.wav (16 kHz mono) + manifest.json.
# NOTE: this is SYNTHETIC speech (two TTS voices), not human recordings; the report says so.
param([string]$Root = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)))

Add-Type -AssemblyName System.Speech
$out = Join-Path $Root "ml\eval_audio"
New-Item -ItemType Directory -Force $out | Out-Null
$data = Join-Path $Root "ml\data"

$items = @()
# unmodified seed sentences from the test split (capitalised == original seed text)
Get-Content (Join-Path $data "test.jsonl") | ForEach-Object {
    $r = $_ | ConvertFrom-Json
    if ($r.text.Length -gt 0 -and [char]::IsUpper($r.text[0])) { $items += [pscustomobject]@{ kind = "clear"; text = $r.text; gold = $r.intent } }
}
Get-Content (Join-Path $data "ambiguous_test.jsonl") | ForEach-Object {
    $r = $_ | ConvertFrom-Json
    $items += [pscustomobject]@{ kind = "ambiguous"; text = $r.text; plausible = @($r.plausible) }
}

$voices = $null
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$voices = $s.GetInstalledVoices() | Where-Object { $_.Enabled -and $_.VoiceInfo.Culture.Name -like "en-*" } | Select-Object -ExpandProperty VoiceInfo
$fmt = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(16000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)

$manifest = @()
for ($i = 0; $i -lt $items.Count; $i++) {
    $v = $voices[$i % $voices.Count]
    $s.SelectVoice($v.Name)
    $file = Join-Path $out ("u{0:D3}.wav" -f $i)
    $s.SetOutputToWaveFile($file, $fmt)
    $s.Speak($items[$i].text)
    $s.SetOutputToNull()
    $e = $items[$i] | Select-Object *
    $e | Add-Member -NotePropertyName file -NotePropertyValue ("u{0:D3}.wav" -f $i)
    $e | Add-Member -NotePropertyName voice -NotePropertyValue $v.Name
    $manifest += $e
}
$s.Dispose()
$manifest | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $out "manifest.json") -Encoding utf8
"Synthesised $($items.Count) utterances with voices: $(($voices | ForEach-Object Name) -join ', ')"
