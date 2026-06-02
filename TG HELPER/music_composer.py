# -*- coding: utf-8 -*-
"""
AI 音乐作曲模块 V4 - 三阶段子Agent架构
Stage1: 主旋律创作 → Stage2: 编曲展开 → Stage3: 完整拼装 → MIDI → 多乐器渲染 → MP3
对标 Suno 的分阶段作曲流程
"""
import os
import struct
import time
import json
import re
import math
import traceback
import numpy as np

SAMPLE_RATE = 44100
TICKS_PER_BEAT = 480

NOTE_TO_MIDI = {
    "C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3, "E": 4, "F": 5,
    "F#": 6, "GB": 6, "G": 7, "G#": 8, "AB": 8, "A": 9, "A#": 10, "BB": 10, "B": 11,
}
DURATION_TO_BEATS = {
    "w": 4.0, "h": 2.0, "q": 1.0, "e": 0.5, "s": 0.25,
    "h.": 3.0, "q.": 1.5, "e.": 0.75, "w.": 6.0,
}
DRUM_NOTES = {
    "kick": 36, "snare": 38, "clap": 39, "hat": 42,
    "ohh": 46, "crash": 49, "ride": 51, "tom_l": 45, "tom_h": 48,
}
GM_INSTRUMENTS = {
    "piano": 0, "grand_piano": 0, "bright_piano": 1, "electric_piano": 4,
    "guitar": 24, "acoustic_guitar": 24, "electric_guitar": 29,
    "bass": 32, "acoustic_bass": 32,
    "violin": 40, "viola": 41, "cello": 42, "contrabass": 43,
    "strings": 48, "harp": 46,
    "trumpet": 56, "trombone": 57, "french_horn": 60,
    "sax": 64, "alto_sax": 65, "oboe": 68, "flute": 73, "clarinet": 71,
    "synth_pad": 88, "synth_lead": 80, "choir": 52,
}
INSTRUMENT_FAMILY = {
    "piano": "piano", "grand_piano": "piano", "bright_piano": "piano", "electric_piano": "piano",
    "guitar": "guitar", "acoustic_guitar": "guitar", "electric_guitar": "guitar",
    "bass": "bass", "acoustic_bass": "bass", "contrabass": "bass",
    "violin": "strings", "viola": "strings", "cello": "strings", "strings": "strings",
    "harp": "strings", "trumpet": "brass", "trombone": "brass", "french_horn": "brass",
    "sax": "woodwind", "alto_sax": "woodwind", "oboe": "woodwind", "flute": "woodwind",
    "clarinet": "woodwind", "synth_pad": "synth", "synth_lead": "synth", "choir": "vocal",
}

# ==================== Stage 1: 主旋律创作 ====================
STAGE1_MELODY_PROMPT = """你是旋律创作大师。输出紧凑文本格式（非JSON），定义主旋律的block和结构。

## 输出格式
只输出以下紧凑文本：

$KEY C
$BPM 120
$TIME 4,4
$INSTR piano

@0 C4q E4q G4q C5h
@1 C4q D4q E4q D4q
@2 E4q F4q G4q C5h
@3 G4q A4q C5q E5h

### motif 16 0.5
[C] C Am F G C Am F G
pno: @0 @1 @2 @3 @2 @1 @0 @3 @0 @1 @0 @1 @2 @1 @0 @3
###

## 规则
- $KEY: 调性 C/D/E/F/G/A/B 加 m=小调 (如 Dm)
- $BPM: 速度 60-200
- $TIME: 拍号 默认4,4
- $INSTR: 乐器列表(空格分隔) 如: piano violin drums bass
- @N: 定义旋律block(N=0-99)，格式: 音符八度时值(空格分隔)
  例: @0 C4q E4q G4q C5h (C4四分+C4八分+G4四分+C5二分)
  时值: w=4拍 h=2拍 q=1拍 e=0.5拍 s=0.25拍
  和弦: @5 C4+E4+G4w (C大三和弦)
  休止: -w (整小节休止)
- ### name bars energy: 段落(至少一个motif段, name=motif, bars=16)
- [C] 后跟和弦名(空格分隔), 每小节一个
- pno: 后跟block引用或直接音符(空格分隔), 每项=一小节
  例: pno: @0 @1 @0 @1 (4小节,使用block0和1交替)
- ### 结束段落
- 可选: $REVERB 0.3 添加混响, $DELAY 0.2 3 0.4 添加延迟

## 写作技巧
- 动机重复+变化: @0 @0 @0_var @0 (同一block的变体)
- 每小节约4个音符保持紧凑
- chord_progression用常见进行: C-G-Am-F, Am-F-C-G等"""



STAGE2_ARRANGE_PROMPT = """你是编曲大师。基于主旋律展开为完整编曲，输出紧凑格式。

## 输出格式
$KEY Dm
$BPM 140
$INSTR piano strings drums bass brass

@0 (复用Stage1的block或新定义)
@1 D4q F4q A4q D5h

### intro 4 0.2
[C] Dm Bb C Dm
pno: -w -w @0 -w
str: @0 -w -w -w
bas: D2h D2h C2h D2h
drm: - h - h
###

### verse 8 0.5
[C] Dm C Bb Am
pno: @0 @1 @0 @1 @1 @0 @1 @0
str: @0 @0 @0 @0 @1 @1 @0 @0
bas: D2h C2h Bb2h A2h
drm: k h s h k h s h
###

### chorus 8 0.8
[C] Dm C Bb Am Dm C Bb Dm
pno: @0 @1 @0 @1 @0 @1 @0 @1
str: @0 @1 @0 @1 @0 @1 @0 @1
bas: D2q C2q Bb2q A2q D2q C2q Bb2q D2q
brs: -w @0 @1 @0 -w @1 @0 -w
drm: k h s k+crash k h s k+crash
###

### outro 4 0.2
[C] Dm Bb Dm Dm
pno: @0 -w -w D4+F4+A4+D5w
str: @0 -w -w -w
bas: D2h Bb2h D2h D2w
drm: - h - crash
###

## 规则
- 每个section至少4个track: pno str bas drm
- 可用乐器码: pno(钢琴) str(弦乐) bas(贝斯) drm(鼓) gtr(吉他) brs(铜管) wnd(木管) syn(合成器) chr(合唱) cel(大提琴) vln(小提琴) hrp(竖琴) org(风琴)
- drm格式: 每拍一个token,空格分隔。可用: k(底鼓) s(军鼓) h(踩镲) o(开镲) c(吊镲) r(叮叮)
  - 复合: k+s (同时)  - (休止)
  - 4/4拍每小节4个token: k h s h
- 每行track数据 = N个元素(N=该section的小节数), 每个元素是一小节
- 同名section用编号区分: verse1 verse2

## 编曲技巧
- chorus的energy最高(0.7-0.9)，多乐器齐奏，密集鼓点
- verse用中等energy，鼓点简单
- intro渐入(energy 0.1-0.3)，outro渐出(energy 0.1-0.2)
- bridge换和弦进行，减少乐器做对比
- 贝斯线紧跟和弦根音，八分音符增加动感
- 不同乐器之间要有呼应和对话
- 可选 $REVERB 0.3 加混响, $DELAY 0.2 3 0.4 加延迟"""



STAGE3_ASSEMBLE_PROMPT = """你是音乐制作人。将编曲组装为完整成品，输出紧凑格式。

## 输出格式 (与Stage2相同,但需确保完整)
$KEY Dm
$BPM 140
$TIME 4,4
$INSTR piano strings drums bass brass

@0 D4q F4q A4q D5h
@1 E4q G4q Bb4q E5h
@2 D4+F4+A4+D5w

### intro 8 0.15
[C] Dm Bb C Dm Dm Bb Am Dm
pno: -w -w -w @0 -w -w @1 -w
str: D3+F3+A3w D3+F3+A3w Bb2+D3+F3w C3+E3+G3w D3+F3+A3w D3+F3+A3w Bb2+D3+F3w A2+C3+E3w D3+F3+A3w
bas: D2w D2w Bb1w C2w D2w D2w Bb1w A1w
drm: - h - h - h - h - - k c
###

### verse1 8 0.45
[C] Dm C Bb Am Dm C Bb Am
pno: @0 @1 @0 @1 @1 @0 @1 @0
str: @2 @2 @2 @2 @2 @2 @2 @2
bas: D2q C2q Bb2q A2q D2q C2q Bb2q A2q
drm: k h s h k h s h
###

### chorus1 8 0.75
[C] Dm C Bb Am Dm C Bb Dm
pno: @0 @1 @0 @1 @0 @1 @0 @1
str: @0 @1 @0 @1 @0 @1 @0 @1
bas: D2q C2q Bb2q A2q D2q C2q Bb2q D2q
brs: -w @0 @1 @0 -w @1 @0 -w
drm: k h s k+c k h s k+c
###

### verse2 8 0.55
[C] Dm Am Bb C Dm Am Bb Dm
pno: @0 @0 @1 @1 @0 @1 @0 @1
str: @1 @1 @0 @0 @1 @0 @1 @0
bas: D2q A2q Bb2q C2q D2q A2q Bb2q D2q
drm: k h s h k h s h
###

### chorus2 8 0.85
[C] Dm C Bb Am Dm C Bb Dm
pno: @0 @1 @0 @1 @0 @1 @0 @1
str: @0 @1 @0 @1 @0 @1 @0 @1
bas: D2e C2e D2e C2e Bb2e A2e Bb2e A2e D2e C2e D2e C2e Bb2e D2e C2e Bb2e
brs: @0 @1 @0 @1 @0 @1 @0 @1
drm: k h s k+c k h s k+s+c
###

### bridge 8 0.4
[C] Bb C Am Dm Bb C Am A
pno: @1 @0 @0 @1 @1 @0 @1 @0
str: Bb2+D3+F3w C3+E3+G3w A2+C3+E3w D3+F3+A3w Bb2+D3+F3w C3+E3+G3w A2+C3+E3w A2+C#3+E3w
bas: Bb2h C2h A2h D2h Bb2h C2h A2h A2h
drm: - h - h s r s r
###

### chorus3 8 0.95
[C] Dm C Bb Am Dm C Bb Dm
pno: @0 @1 @0 @1 @0 @1 @0 @1
str: @0 @1 @0 @1 @0 @1 @0 @1
bas: D2s C2s D2s C2s Bb2s A2s Bb2s A2s D2s C2s D2s C2s Bb2s D2s C2s D2s
brs: @0 @1 @0 @1 @0 @1 @0 @1
drm: k h s k+c k h s k+s+crash
###

### outro 8 0.1
[C] Dm Bb Dm Dm Dm Bb Dm Dm
pno: @0 -w @2 -w @1 -w -w D4+F4+A4+D5w
str: D3+F3+A3w -w D3+F3+A3w -w D3+F3+A3w -w -w D3+F3+A3+D5w
bas: D2w -w D2w -w D2w -w -w D2w
drm: - - - - - - - c
###

## 核心约束
- 总时长≥3分钟(约90小节@120BPM)
- 每行track的元素数必须等于该section的bars数
- chorus1→chorus2→chorus3 能量递增(0.75→0.85→0.95)
- intro能量<0.2，outro能量<0.15
- bridge换和弦/节奏做对比
- 完整结构: intro→verse1→(pre)chorus1→verse2→(pre)chorus2→bridge→chorus3→outro

## 音效设置(可选)
在歌曲开头(全局)或任何section内添加音效:
- $SWING 0.15        # 摇摆感 0-0.3，延迟弱拍增加groove
- $REVERB 0.4        # 混响量 0-1，推荐0.2-0.5
- $DELAY 0.2 3 0.4   # 延迟量 0-0.7, 回声节拍数, 反馈量0-0.85
- $FILTER lp 8000    # 低通滤波(lp/lowpass), Hz
- $FILTER hp 60      # 高通滤波(hp/highpass), Hz
  例: 全局加混响 → 在$BPM后加 $REVERB 0.35
  例: bridge加混响 → 在bridge段内加 $REVERB 0.5
"""



# ==================== 音频合成 ====================

def _midi_to_freq(note):
    return 440.0 * (2 ** ((note - 69) / 12.0))


def _simple_lowpass(audio, cutoff=4000):
    if len(audio) <= 1:
        return audio
    rc = 1.0 / (2.0 * math.pi * cutoff)
    dt = 1.0 / SAMPLE_RATE
    alpha = dt / (rc + dt)
    f = np.zeros_like(audio)
    f[0] = audio[0]
    for i in range(1, len(audio)):
        f[i] = f[i - 1] + alpha * (audio[i] - f[i - 1])
    return f


def _simple_highpass(audio, cutoff=4000):
    if len(audio) <= 1:
        return audio
    rc = 1.0 / (2.0 * math.pi * cutoff)
    dt = 1.0 / SAMPLE_RATE
    alpha = rc / (rc + dt)
    f = np.zeros_like(audio)
    f[0] = audio[0]
    for i in range(1, len(audio)):
        f[i] = alpha * (f[i - 1] + audio[i] - audio[i - 1])
    return f


def _synth_piano(freq, n, vel=80):
    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE
    env = np.exp(-t * 3.5) * 0.9 + np.exp(-t * 12) * 0.1
    w = np.sin(2*np.pi*freq*t) + np.sin(4*np.pi*freq*t)*0.5 + np.sin(6*np.pi*freq*t)*0.25
    w += np.sin(8*np.pi*freq*t)*0.12 + np.sin(10*np.pi*freq*t)*0.06
    return w * env * (vel / 127 * 0.5)


def _synth_strings(freq, n, vel=80):
    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE
    a_samp = max(1, int(min(0.15, n/SAMPLE_RATE*0.3) * SAMPLE_RATE))
    env = np.ones(n, dtype=np.float64)
    if a_samp < n:
        env[:a_samp] = np.linspace(0, 1, a_samp)
    vib = 1.0 + np.sin(2*np.pi*5.5*t) * 0.005
    phase = 2 * np.pi * freq * t * vib
    saw = 2 * ((phase / (2*np.pi)) % 1) - 1
    saw = _simple_lowpass(saw, 8000)
    return saw * env * (vel / 127 * 0.35)


def _synth_cello(freq, n, vel=80):
    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE
    a_samp = max(1, int(min(0.2, n/SAMPLE_RATE*0.35) * SAMPLE_RATE))
    env = np.ones(n, dtype=np.float64)
    if a_samp < n:
        env[:a_samp] = np.linspace(0, 1, a_samp)
    vib = 1.0 + np.sin(2*np.pi*5.0*t) * 0.004
    phase = 2 * np.pi * freq * t * vib
    saw = 2 * ((phase / (2*np.pi)) % 1) - 1
    saw = np.clip(saw * 1.2, -1, 1)
    return saw * env * (vel / 127 * 0.28)


def _synth_guitar(freq, n, vel=80):
    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE
    w = np.sin(2*np.pi*freq*t) + np.sin(4*np.pi*freq*t)*0.7 + np.sin(6*np.pi*freq*t)*0.5
    w += np.sin(8*np.pi*freq*t)*0.3 + np.sin(12*np.pi*freq*t)*0.15
    env = np.exp(-t * 4) * 0.9 + np.exp(-t * 20) * 0.1
    return w * env * (vel / 127 * 0.4)


def _synth_brass(freq, n, vel=80):
    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE
    a_samp = max(1, int(0.03 * SAMPLE_RATE))
    env = np.ones(n, dtype=np.float64)
    if a_samp < n:
        env[:a_samp] = np.linspace(0, 1, a_samp)
    phase = 2 * np.pi * freq * t
    w = 2 * ((phase / (2*np.pi)) % 1) - 1
    w += np.sin(phase*2)*0.3 + np.sin(phase*3)*0.15
    return w * env * (vel / 127 * 0.4)


def _synth_woodwind(freq, n, vel=80):
    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE
    a_samp = max(1, int(0.06 * SAMPLE_RATE))
    env = np.ones(n, dtype=np.float64)
    if a_samp < n:
        env[:a_samp] = np.linspace(0, 1, a_samp)
    r_start = max(0, n - int(0.03 * SAMPLE_RATE))
    env[r_start:] = np.linspace(1, 0, n - r_start)
    w = np.sin(2*np.pi*freq*t) + np.sin(4*np.pi*freq*t)*0.2
    w += (np.random.randn(n) * 0.02)
    return w * env * (vel / 127 * 0.35)


def _synth_bass(freq, n, vel=80):
    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE
    env = np.exp(-t * 8) * 0.7 + np.ones(n) * 0.3
    w = np.sin(2*np.pi*freq*t)*0.7 + np.sin(4*np.pi*freq*t)*0.2 + np.sin(6*np.pi*freq*t)*0.1
    return _simple_lowpass(w * env * (vel / 127 * 0.5), 800)


def _synth_synth(freq, n, vel=80):
    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE
    a_samp = max(1, int(0.05 * SAMPLE_RATE))
    env = np.ones(n, dtype=np.float64)
    if a_samp < n:
        env[:a_samp] = np.linspace(0, 1, a_samp)
    r_start = max(0, n - int(0.08 * SAMPLE_RATE))
    env[r_start:] = np.linspace(1, 0, n - r_start)
    phase = 2 * np.pi * freq * t
    saw = 2 * ((phase / (2*np.pi)) % 1) - 1
    return _simple_lowpass(saw * env * (vel / 127 * 0.35), 3000)


def _synth_choir(freq, n, vel=80):
    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE
    a_samp = max(1, int(min(0.25, n/SAMPLE_RATE*0.4) * SAMPLE_RATE))
    env = np.ones(n, dtype=np.float64)
    if a_samp < n:
        env[:a_samp] = np.linspace(0, 1, a_samp)
    r_start = max(0, n - int(0.2 * SAMPLE_RATE))
    env[r_start:] = np.linspace(1, 0, n - r_start)
    w = np.sin(2*np.pi*freq*t)*0.6 + np.sin(4*np.pi*freq*t)*0.25
    w += np.sin(6*np.pi*freq*t)*0.1 + np.sin(np.pi*freq*t)*0.08
    return w * env * (vel / 127 * 0.5)


def _synth_drum(drum_note, beat_dur):
    ns = int(beat_dur * SAMPLE_RATE * 0.8)
    if ns <= 0:
        return np.array([], dtype=np.float64)
    t = np.arange(ns, dtype=np.float64) / SAMPLE_RATE
    if drum_note == 36:
        fe = np.maximum(150 - t * 120, 30)
        phase = 2 * np.pi * np.cumsum(fe) / SAMPLE_RATE
        return np.sin(phase) * np.exp(-t * 8) * 0.7
    elif drum_note == 38:
        return np.random.randn(ns) * 0.55 * np.exp(-t * 10)
    elif drum_note == 42:
        return _simple_highpass(np.random.randn(ns) * 0.25 * np.exp(-t * 25), 6000)
    elif drum_note == 49:
        return _simple_highpass(np.random.randn(ns) * 0.4 * np.exp(-t * 5), 8000)
    elif drum_note == 46:
        return _simple_highpass(np.random.randn(ns) * 0.3 * np.exp(-t * 15), 5000)
    elif drum_note == 51:
        return _simple_highpass(np.random.randn(ns) * 0.2 * np.exp(-t * 20), 7000)
    return np.zeros(ns, dtype=np.float64)


INSTRUMENT_SYNTH = {
    "piano": _synth_piano, "grand_piano": _synth_piano, "bright_piano": lambda f,n,v: _synth_piano(f,n,v)*1.2,
    "electric_piano": lambda f,n,v: _synth_piano(f,n,v)*_simple_lowpass(np.sin(2*math.pi*f*np.arange(n)/SAMPLE_RATE),3000),
    "guitar": _synth_guitar, "acoustic_guitar": _synth_guitar,
    "electric_guitar": lambda f,n,v: _synth_guitar(f,n,v)*1.3,
    "bass": _synth_bass, "acoustic_bass": _synth_bass, "contrabass": _synth_bass,
    "violin": _synth_strings, "viola": lambda f,n,v: _synth_strings(f,n,min(v,75)),
    "cello": _synth_cello, "strings": _synth_strings,
    "harp": lambda f,n,v: _synth_guitar(f,n,v)*0.8,
    "trumpet": _synth_brass, "trombone": lambda f,n,v: _synth_brass(f,n,v)*0.9,
    "french_horn": lambda f,n,v: _synth_brass(f,n,v)*0.7,
    "sax": lambda f,n,v: _synth_brass(f,n,v)*1.1, "alto_sax": lambda f,n,v: _synth_brass(f,n,v)*1.1,
    "oboe": _synth_woodwind, "flute": _synth_woodwind,
    "clarinet": lambda f,n,v: _synth_woodwind(f,n,v)*0.9,
    "synth_pad": _synth_synth, "synth_lead": lambda f,n,v: _synth_synth(f,n,v)*1.2,
    "choir": _synth_choir,
    "organ": lambda f,n,v: _synth_choir(f,n,v)*0.6 + _synth_brass(f,n,v)*0.4,
    "marimba": lambda f,n,v: _synth_piano(f,n,int(v*0.6))*1.5,
    "bell": lambda f,n,v: (np.sin(2*np.pi*f*np.arange(n)/SAMPLE_RATE)*np.exp(-np.arange(n)/SAMPLE_RATE/0.5)*0.5
                           + np.sin(4*np.pi*f*np.arange(n)/SAMPLE_RATE)*np.exp(-np.arange(n)/SAMPLE_RATE/0.3)*0.3
                           + np.sin(6*np.pi*f*np.arange(n)/SAMPLE_RATE)*np.exp(-np.arange(n)/SAMPLE_RATE/0.15)*0.2),
    "pad": _synth_synth,
    "lead": lambda f,n,v: _synth_synth(f,n,v)*1.3,
    "pluck": lambda f,n,v: _synth_guitar(f,n,v)*1.1,
}

COMPACT_DRUM_MAP = {
    "k": "kick", "s": "snare", "h": "hat", "o": "ohh",
    "c": "crash", "r": "ride", "tl": "tom_l", "th": "tom_h",
    "kick": "kick", "snare": "snare", "hat": "hat", "ohh": "ohh",
    "crash": "crash", "ride": "ride", "tom_l": "tom_l", "tom_h": "tom_h",
    "clap": "clap",
}

TOKEN_INSTR_MAP = {
    "pno": "piano", "piano": "piano",
    "str": "strings", "strings": "strings", "string": "strings",
    "bas": "bass", "bass": "bass",
    "drm": "drums", "drums": "drums", "drum": "drums",
    "gtr": "guitar", "guitar": "guitar",
    "brs": "trumpet", "brass": "trumpet", "trumpet": "trumpet",
    "wnd": "flute", "woodwind": "flute", "flute": "flute",
    "syn": "synth_pad", "synth": "synth_pad",
    "chr": "choir", "choir": "choir",
    "cel": "cello", "cello": "cello",
    "vln": "violin", "violin": "violin",
    "hrp": "harp", "harp": "harp",
    "org": "organ", "organ": "organ",
    "sax": "sax", "saxophone": "sax",
    "bel": "bell", "bell": "bell",
    "pad": "pad", "lead": "lead", "pluck": "pluck",
    "mar": "marimba", "marimba": "marimba",
}


# ==================== 音频效果引擎 ====================

def _apply_reverb(audio, wet=0.3, room_size=0.5, sample_rate=SAMPLE_RATE):
    """Schroeder 混响: 4个并联梳状滤波器 + 2个串联全通滤波器"""
    if wet <= 0 or len(audio) < 100:
        return audio
    wet = min(wet, 0.9)
    delay_lens = [
        int(sample_rate * 0.0297), int(sample_rate * 0.0371),
        int(sample_rate * 0.0411), int(sample_rate * 0.0437),
    ]
    comb_gains = [0.8, 0.79, 0.78, 0.77]
    ap_delays = [int(sample_rate * 0.005), int(sample_rate * 0.0017)]
    ap_gain = 0.5
    out = np.zeros_like(audio)
    for i, (dl, cg) in enumerate(zip(delay_lens, comb_gains)):
        buf = np.zeros(dl)
        g = cg * (0.6 + room_size * 0.4)
        for n in range(len(audio)):
            idx = n % dl
            delayed = buf[idx]
            buf[idx] = audio[n] + g * delayed
            out[n] += delayed
    out = out / 4.0
    for ap_delay in ap_delays:
        buf = np.zeros(ap_delay)
        for n in range(len(out)):
            idx = n % ap_delay
            delayed = buf[idx]
            buf[idx] = out[n] + ap_gain * delayed
            out[n] = delayed - ap_gain * buf[idx]
    return audio * (1.0 - wet * 0.7) + out * wet


def _apply_delay(audio, wet=0.2, delay_beats=3, feedback=0.35, bpm=120, sample_rate=SAMPLE_RATE):
    """反馈延迟/回声效果"""
    if wet <= 0 or len(audio) < 100:
        return audio
    wet = min(wet, 0.7)
    delay_samples = int((60.0 / bpm) * delay_beats * sample_rate)
    if delay_samples <= 0 or delay_samples >= len(audio):
        return audio
    out = audio.copy()
    fb = min(feedback, 0.85)
    for n in range(delay_samples, len(audio)):
        out[n] += out[n - delay_samples] * fb
    mx = np.max(np.abs(out))
    if mx > 0:
        out = out / mx * 0.9
    return audio * (1.0 - wet) + out * wet


def _apply_eq(audio, lowcut=0, highcut=20000, sample_rate=SAMPLE_RATE):
    """简易EQ: 低切/高切滤波"""
    result = audio.copy()
    if highcut and highcut < 20000:
        result = _simple_lowpass(result, highcut)
    if lowcut and lowcut > 20:
        result = _simple_highpass(result, lowcut)
    return result


# ==================== 和弦映射 ====================

CHORD_FORMULAS = {
    "": [0, 4, 7], "m": [0, 3, 7], "M": [0, 4, 7],
    "7": [0, 4, 7, 10], "m7": [0, 3, 7, 10], "M7": [0, 4, 7, 11],
    "dim": [0, 3, 6], "aug": [0, 4, 8],
    "sus2": [0, 2, 7], "sus4": [0, 5, 7],
    "6": [0, 4, 7, 9], "m6": [0, 3, 7, 9],
    "9": [0, 4, 7, 10, 14], "m9": [0, 3, 7, 10, 14],
    "5": [0, 7],
}

CHORD_ROOT_MAP = {
    "C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3, "E": 4,
    "F": 5, "F#": 6, "GB": 6, "G": 7, "G#": 8, "AB": 8,
    "A": 9, "A#": 10, "BB": 10, "B": 11,
}


def _chord_to_midi_notes(chord_name, base_octave=3):
    """将和弦名映射为 MIDI 音符列表，如 C → [48,52,55]  Am7 → [45,48,52,55]"""
    if not chord_name:
        return []
    name = chord_name.strip()
    m = re.match(r'^([A-G][#B]?)(m?)(\d*)$', name, re.IGNORECASE)
    if not m:
        quarters = name.split("/")[0].strip() if "/" in name else name
        m2 = re.match(r'^([A-G][#B]?)(.*)$', quarters, re.IGNORECASE)
        if not m2:
            return []
        root_str = m2.group(1)
        suffix = m2.group(2).strip()
    else:
        root_str = m.group(1)
        is_minor = "m" if m.group(2) == "m" else ""
        suffix = is_minor + m.group(3)

    root_offset = CHORD_ROOT_MAP.get(root_str.upper(), 0)
    formula = CHORD_FORMULAS.get(suffix, CHORD_FORMULAS.get("", [0, 4, 7]))
    root_midi = 12 * (base_octave + 1) + root_offset
    return [root_midi + interval for interval in formula]


def _correct_note_to_chord(midi_note, chord_midi_notes):
    """如果音符不在和弦中，移到最近的和弦音"""
    if not chord_midi_notes:
        return midi_note
    note_class = midi_note % 12
    chord_classes = [n % 12 for n in chord_midi_notes]
    if note_class in chord_classes:
        return midi_note
    distances = [min(abs(note_class - cc), 12 - abs(note_class - cc)) for cc in chord_classes]
    best = distances.index(min(distances))
    target_class = chord_classes[best]
    if note_class > target_class:
        if note_class - target_class > 6:
            return midi_note + (12 - (note_class - target_class))
        else:
            return midi_note - (note_class - target_class)
    else:
        if target_class - note_class > 6:
            return midi_note - (12 - (target_class - note_class))
        else:
            return midi_note + (target_class - note_class)


# ==================== 音质增强 ====================

def _apply_stereo_width(audio, width=0.6, sample_rate=SAMPLE_RATE):
    """伪立体声：Haas效应 + 互补梳状滤波"""
    if width <= 0 or len(audio) < 100:
        return audio
    delay_samp = int(sample_rate * 0.008 * width)
    left = audio.copy()
    right = np.roll(audio, delay_samp) if delay_samp > 0 else audio.copy()
    if delay_samp > 0:
        right[:delay_samp] = 0
    left = left * (1 - width * 0.3) + right * width * 0.15
    right = right * (1 - width * 0.3) + left * width * 0.15
    return np.column_stack((left, right)) if left.ndim == 1 else np.column_stack((left, right))


def _apply_warmth(audio, amount=0.08):
    """软饱和增加温暖度"""
    if amount <= 0 or len(audio) < 10:
        return audio
    wet = np.tanh(audio * (1.5 + amount * 3))
    return audio * (1 - amount) + wet * amount


# ==================== 人性化 ====================

_HUMANIZE_SEED = None


def _reset_humanize_seed():
    global _HUMANIZE_SEED
    _HUMANIZE_SEED = int(time.time() * 1000) % 100000


def _humanize_vel(vel, amount=0.12):
    """随机力度变化 ±12%，确定性随机"""
    global _HUMANIZE_SEED
    if _HUMANIZE_SEED is None:
        _reset_humanize_seed()
    _HUMANIZE_SEED = (_HUMANIZE_SEED * 1103515245 + 12345) & 0x7FFFFFFF
    r = ((_HUMANIZE_SEED % 1000) / 1000.0 - 0.5) * 2 * amount
    return max(10, min(127, int(vel * (1.0 + r))))


def _humanize_time(amount_ms=3):
    """随机微时偏移 ±3ms，确定性随机"""
    global _HUMANIZE_SEED
    if _HUMANIZE_SEED is None:
        _reset_humanize_seed()
    _HUMANIZE_SEED = (_HUMANIZE_SEED * 1103515245 + 12345) & 0x7FFFFFFF
    r = ((_HUMANIZE_SEED % 1000) / 1000.0 - 0.5) * 2 * amount_ms / 1000.0
    return r


# ==================== 音符解析 ====================

def _parse_note_compact(note_str):
    """解析紧凑格式音符: C4q E4e G4+E4h """
    note_str = note_str.strip()
    if note_str in ("-", "-w", "r"):
        return None
    match = re.match(r'^([A-G][#B]?\d(?:[\+][A-G][#B]?\d)*)([whqes]\.?)$', note_str, re.IGNORECASE)
    if not match:
        return None
    notes_part, dur_part = match.group(1), match.group(2).lower()
    dur_beats = DURATION_TO_BEATS.get(dur_part, 1.0)
    midis = []
    for n in notes_part.split("+"):
        m = re.match(r'^([A-G][#B]?)(\d)$', n, re.IGNORECASE)
        if m:
            midi = NOTE_TO_MIDI.get(m.group(1).upper().replace("B", "B"), 0)
            if m.group(1).endswith("B"):
                midi = NOTE_TO_MIDI.get(m.group(1).upper(), 0)
            midis.append(midi + (int(m.group(2)) + 1) * 12)
    if midis:
        return (midis, dur_beats)
    return None


def _parse_token_music(text):
    """解析紧凑 Token 格式音乐文本 → 内部 music_data 字典"""
    if not text or not text.strip():
        return None
    lines = text.strip().split("\n")

    music = {
        "title": "Untitled",
        "key": "C", "mode": "major", "bpm": 120, "time": [4, 4],
        "instruments": {},
        "sections": [],
        "effects": {"reverb": 0.0, "delay": 0.0, "delay_beats": 3, "feedback": 0.35,
                    "lowcut": 0, "highcut": 0},
        "swing": 0.0,
    }
    blocks = {}
    current_section = None
    current_chords = []
    current_tracks = {}
    current_effects = {}

    inst_full_names = set()

    def _detect_mode(key_str):
        return "minor" if key_str and "m" in key_str.lower() else "major"

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("$TITLE") or line.startswith("$TITLE:"):
            music["title"] = line.split(None, 1)[1].strip() if len(line.split(None, 1)) > 1 else "Untitled"
            continue
        if line.startswith("$KEY") or line.startswith("$KEY:"):
            v = line.split(None, 1)[1].strip() if len(line.split(None, 1)) > 1 else "C"
            music["key"] = v.replace("m", "").replace("M", "").strip()
            music["mode"] = _detect_mode(v)
            continue
        if line.startswith("$BPM") or line.startswith("$BPM:"):
            v = line.split(None, 1)[1].strip() if len(line.split(None, 1)) > 1 else "120"
            try:
                music["bpm"] = int(v)
            except:
                music["bpm"] = 120
            continue
        if line.startswith("$TIME") or line.startswith("$TIME:"):
            v = line.split(None, 1)[1].strip() if len(line.split(None, 1)) > 1 else "4,4"
            parts = v.replace(",", " ").split()
            music["time"] = [int(parts[0]) if parts else 4, int(parts[1]) if len(parts) > 1 else 4]
            continue

        if line.startswith("$INSTR") or line.startswith("$INSTR:"):
            v = line.split(None, 1)[1].strip() if len(line.split(None, 1)) > 1 else ""
            for w in v.split():
                mapped = TOKEN_INSTR_MAP.get(w.lower(), w.lower())
                inst_full_names.add(mapped)
            continue

        if line.startswith("$SWING") or line.startswith("$SWING:"):
            parts = line.split(None, 1)
            val = float(parts[1].strip()) if len(parts) > 1 else 0.15
            music["swing"] = max(0.0, min(val, 0.35))
            continue

        if line.startswith("$REVERB") or line.startswith("$REVERB:"):
            parts = line.split(None, 1)
            val = float(parts[1].strip()) if len(parts) > 1 else 0.3
            if current_section:
                current_effects["reverb"] = max(0.0, min(val, 1.0))
            else:
                music["effects"]["reverb"] = max(0.0, min(val, 1.0))
            continue
        if line.startswith("$DELAY") or line.startswith("$DELAY:"):
            parts = line.split(None, 1)[1].strip().split() if len(line.split(None, 1)) > 1 else ["0.2", "3", "0.35"]
            wet = float(parts[0]) if parts else 0.2
            beats = float(parts[1]) if len(parts) > 1 else 3
            fb = float(parts[2]) if len(parts) > 2 else 0.35
            if current_section:
                current_effects["delay"] = max(0.0, min(wet, 0.7))
                current_effects["delay_beats"] = max(1, min(beats, 16))
                current_effects["feedback"] = max(0.0, min(fb, 0.85))
            else:
                music["effects"]["delay"] = max(0.0, min(wet, 0.7))
                music["effects"]["delay_beats"] = max(1, min(beats, 16))
                music["effects"]["feedback"] = max(0.0, min(fb, 0.85))
            continue
        if line.startswith("$FILTER") or line.startswith("$FILTER:"):
            parts = line.split(None, 1)[1].strip().split() if len(line.split(None, 1)) > 1 else []
            for i in range(0, len(parts), 2):
                if i + 1 < len(parts):
                    try:
                        ftype = parts[i].lower()
                        fval = float(parts[i + 1])
                        if ftype in ("lp", "lowpass"):
                            if current_section:
                                current_effects["highcut"] = fval
                            else:
                                music["effects"]["highcut"] = fval
                        elif ftype in ("hp", "highpass"):
                            if current_section:
                                current_effects["lowcut"] = fval
                            else:
                                music["effects"]["lowcut"] = fval
                    except:
                        pass
            continue

        if line.startswith("@") and (" " in line or "\t" in line):
            parts = line[1:].split(None, 1)
            if len(parts) >= 2:
                bid = parts[0].strip()
                notes = parts[1].strip()
                blocks[bid] = notes
            continue

        if line.startswith("###"):
            if current_section and current_tracks:
                sec_data = current_section.copy()
                sec_data["chords"] = current_chords[:]
                sec_data["tracks"] = dict(current_tracks)
                sec_data["effects"] = dict(current_effects)
                music["sections"].append(sec_data)
            parts = line.split()
            name = parts[1] if len(parts) > 1 else "section"
            bars = int(parts[2]) if len(parts) > 2 else 4
            energy = float(parts[3]) if len(parts) > 3 else 0.5
            current_section = {"name": name, "bars": bars, "energy": energy}
            current_chords = []
            current_tracks = {}
            current_effects = {}
            continue

        if line.startswith("[C]") or line.startswith("[C]:"):
            v = line.split(None, 1)[1].strip() if len(line.split(None, 1)) > 1 else line[3:].strip()
            current_chords = v.split()
            continue

        if ":" in line and current_section is not None:
            instr_token, _, data = line.partition(":")
            instr_token = instr_token.strip().lower()
            mapped_instr = TOKEN_INSTR_MAP.get(instr_token)
            if mapped_instr:
                items = data.strip().split()
                resolved = []
                for item in items:
                    if item.startswith("@") and item[1:] in blocks:
                        resolved.append(blocks[item[1:]])
                    else:
                        resolved.append(item)
                current_tracks[mapped_instr] = resolved
            continue

    if current_section and current_tracks:
        sec_data = current_section.copy()
        sec_data["chords"] = current_chords[:]
        sec_data["tracks"] = dict(current_tracks)
        sec_data["effects"] = dict(current_effects)
        music["sections"].append(sec_data)

    if not music["sections"]:
        print("[MusicComposer] 错误: 未找到任何section数据")
        return None

    for inst_name in inst_full_names:
        mapped = TOKEN_INSTR_MAP.get(inst_name, inst_name)
        if mapped not in music["instruments"]:
            music["instruments"][inst_name] = mapped
    if not music["instruments"]:
        print("[MusicComposer] 错误: 未找到 $INSTR 声明")
        return None

    bar_dur = (60.0 / music["bpm"]) * music["time"][0]
    total_secs = sum(s["bars"] * bar_dur for s in music["sections"])
    music["duration_sec"] = total_secs

    print(f"[MusicComposer] Token解析完成: {len(music['sections'])}段, "
          f"{len(music['instruments'])}种乐器, {len(blocks)}个block, "
          f"总时长≈{total_secs:.0f}s")
    return music



# ==================== 依赖检查 ====================

_dependency_errors = []

def _check_dependencies():
    global _dependency_errors
    _dependency_errors = []
    try:
        import numpy as np
    except ImportError:
        _dependency_errors.append("numpy 未安装，请执行: pip install numpy")
    try:
        from openai import OpenAI
    except ImportError:
        _dependency_errors.append("openai 未安装，请执行: pip install openai")
    try:
        from config import config
    except ImportError:
        _dependency_errors.append("config.py 无法导入，请检查项目文件是否完整")
    return _dependency_errors


# ==================== AI 调用 ====================

def _call_ai(system_prompt, user_prompt, max_tokens=8000):
    try:
        from config import config
    except ImportError as e:
        return ("ERROR: config.py 模块导入失败，请检查项目文件完整性。"
                f"\n详细信息: {e}")
    try:
        from openai import OpenAI
    except ImportError as e:
        return ("ERROR: openai 库未安装，AI音乐生成无法工作。"
                f"\n请执行: pip install openai"
                f"\n详细信息: {e}")

    api_key = config.ai_api_key
    if not api_key:
        return ("ERROR: 未配置 AI API Key。\n"
                "请在 config.json 中设置 ai_api_key 字段，"
                "或在设置界面中填写 API Key。")

    base_url = getattr(config, 'ai_base_url', 'https://api.openai.com/v1')
    if not base_url:
        return ("ERROR: 未配置 AI API Base URL。\n"
                "请在 config.json 中设置 ai_base_url 字段。")

    ai_model = getattr(config, 'ai_model', '')
    if not ai_model:
        return ("ERROR: 未配置 AI 模型名称。\n"
                "请在 config.json 中设置 ai_model 字段，"
                "例如: gpt-4o, deepseek-chat, kimi-k2.5 等。")

    client = OpenAI(api_key=api_key, base_url=base_url)

    def _api_call(cur_tokens):
        kwargs = dict(
            model=ai_model,
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_prompt}],
            temperature=0.8, max_tokens=cur_tokens,
            timeout=180)
        if getattr(config, 'deepseek_thinking_enabled', False):
            extra_body = {"thinking": {"type": "enabled"}}
            reasoning_effort = getattr(config, 'deepseek_reasoning_effort', None)
            if reasoning_effort:
                extra_body["reasoning_effort"] = reasoning_effort
            kwargs["extra_body"] = extra_body
        return client.chat.completions.create(**kwargs)

    MAX_RETRIES = 2
    cur_tokens = max_tokens
    last_content = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = _api_call(cur_tokens)
        except Exception as e:
            err_str = str(e)
            if "401" in err_str or "Unauthorized" in err_str:
                hint = "API Key 无效或已过期，请检查 config.json 中的 ai_api_key。"
            elif "404" in err_str or "model_not_found" in err_str.lower():
                hint = f"模型 {ai_model} 未找到，请检查 config.json 中的 ai_model 是否正确。"
            elif "429" in err_str or "rate_limit" in err_str.lower():
                hint = "API 请求频率过高被限流，请稍后重试。"
            elif "402" in err_str or "insufficient_quota" in err_str.lower():
                hint = "API 账户余额不足，请充值后重试。"
            elif "timeout" in err_str.lower() or "timed out" in err_str.lower():
                hint = "API 请求超时（180秒），请检查网络连接或 API 服务状态。"
            elif "connection" in err_str.lower() or "connect" in err_str.lower():
                hint = f"无法连接到 API 服务器 ({base_url})，请检查网络或 ai_base_url 配置。"
            else:
                hint = f"API 调用异常: {err_str}"
            print(f"[MusicComposer] AI调用失败: {hint}")
            traceback.print_exc()
            return f"ERROR: {hint}"

        if not resp.choices:
            return "ERROR: AI 返回了空的 choices 列表，请检查模型配置或 API 账户余额。"

        finish_reason = getattr(resp.choices[0], 'finish_reason', None)
        content = resp.choices[0].message.content

        if finish_reason == "length":
            if content and content.strip():
                last_content = content
            cur_tokens *= 2
            if cur_tokens > 128000:
                cur_tokens = 128000
            if attempt < MAX_RETRIES:
                print(f"[MusicComposer] 输出被截断，自动扩大 max_tokens → {cur_tokens} 重试...")
                continue
            if not content or not content.strip():
                return (f"ERROR: AI 响应被截断（max_tokens={cur_tokens} 不足），"
                        f"请尝试缩短 duration。")
            print(f"[MusicComposer] 警告: 经 {MAX_RETRIES} 次重试仍被截断，"
                  f"JSON 可能不完整，将尝试解析现有内容。")
            return content

        if not content or not content.strip():
            return "ERROR: AI 返回了空内容，可能是模型限制或 API 余额不足。"

        return content

    if last_content:
        return last_content
    return "ERROR: AI 多次重试均未返回有效内容。"


# ==================== 三阶段流水线 ====================

def _stage1_compose_melody(prompt, key, duration):
    """Stage 1: 创作主旋律（Token格式）"""
    user = (f"创作一段主旋律（紧凑格式）：{prompt}\n"
            f"调性：{key}，时长约{duration}秒。\n"
            f"输出格式：$KEY $BPM $TIME + @block定义 + ### motif段 + track数据")
    print("[MusicComposer] Stage1: 创作主旋律...")
    raw = _call_ai(STAGE1_MELODY_PROMPT, user, 4000)
    if isinstance(raw, str) and raw.startswith("ERROR:"):
        print(f"[MusicComposer] Stage1 AI调用失败: {raw}")
        return {"error": raw}
    if not raw:
        return {"error": "ERROR: Stage1 AI调用返回空内容。"}
    data = _parse_token_music(raw)
    if not data:
        err_msg = f"ERROR: Stage1 Token解析失败。AI返回内容:\n{raw[:500]}"
        print(f"[MusicComposer] {err_msg}")
        return {"error": err_msg}
    print(f"[MusicComposer] Stage1 完成: {len(data['sections'])}段, "
          f"{len(data['instruments'])}种乐器, bars={sum(s['bars'] for s in data['sections'])}")
    return data


def _stage2_develop_arrangement(motif, prompt, duration):
    """Stage 2: 围绕主旋律展开编曲"""
    if isinstance(motif, dict) and "error" in motif:
        return {"error": f"ERROR: Stage2 无法执行，因为 Stage1 失败: {motif['error']}"}

    bpm = motif.get("bpm", 120)
    beat_sec = 60.0 / bpm
    bars_per_section = max(8, int(duration * 0.15 / (beat_sec * 4)))
    total_sections = max(6, int(duration / (bars_per_section * beat_sec * 4)))

    user = (f"""基于以下主旋律展开编曲（≥{duration}秒，约{total_sections}段，每段{bars_per_section}小节）：

【主旋律 Token 数据】
{json.dumps(motif, ensure_ascii=False, indent=2)[:1500]}

【要求】
- 至少{total_sections}段: intro/verse1/chorus1/verse2/chorus2/bridge/chorus3/outro
- 复用主旋律的 @block，展开到各段
- 必须包含: pno str bas drm 四个基础track
- chorus energy 0.7-0.9，intro 0.1-0.3，outro 0.05-0.15
- 输出紧凑格式，完整填充每个section的tracks

用户需求: {prompt}""")
    print(f"[MusicComposer] Stage2: 编曲展开 (目标≥{total_sections}段)...")
    raw = _call_ai(STAGE2_ARRANGE_PROMPT, user, 8000)
    if isinstance(raw, str) and raw.startswith("ERROR:"):
        print(f"[MusicComposer] Stage2 AI调用失败: {raw}")
        return {"error": raw}
    if not raw:
        return {"error": "ERROR: Stage2 AI调用返回空内容。"}
    data = _parse_token_music(raw)
    if not data:
        err_msg = f"ERROR: Stage2 Token解析失败。AI返回内容:\n{raw[:500]}"
        print(f"[MusicComposer] {err_msg}")
        return {"error": err_msg}
    print(f"[MusicComposer] Stage2 完成: {len(data['sections'])}段, "
          f"{len(data['instruments'])}种乐器")
    return data


def _stage3_assemble_song(arrangement, prompt, duration):
    """Stage 3: 拼装完整歌曲"""
    if isinstance(arrangement, dict) and "error" in arrangement:
        return {"error": f"ERROR: Stage3 无法执行，因为 Stage2 失败: {arrangement['error']}"}

    secs = arrangement.get("sections", [])
    bars_total = sum(s.get("bars", 4) for s in secs)
    total_s = sum(s.get("bars", 4) * (60.0 / arrangement.get("bpm", 120)) * arrangement.get("time", [4, 4])[0] for s in secs)

    user = (f"""将以下编曲组装为完整歌曲（≥{duration}秒，约90小节@120BPM）：

【编曲数据】
{json.dumps(arrangement, ensure_ascii=False)[:2000]}

【要求】
- 确保总时长≥3分钟，不够就扩展section的bars数
- intro→verse1→chorus1→verse2→chorus2→bridge→chorus3→outro
- chorus1/2/3 能量递增
- 每行track元素数=该段bars数
- outro用长音结束

用户需求: {prompt}""")
    print(f"[MusicComposer] Stage3: 完整拼装...")
    raw = _call_ai(STAGE3_ASSEMBLE_PROMPT, user, 8000)
    if isinstance(raw, str) and raw.startswith("ERROR:"):
        print(f"[MusicComposer] Stage3 AI调用失败: {raw}")
        return {"error": raw}
    if not raw:
        return {"error": "ERROR: Stage3 AI调用返回空内容。"}
    data = _parse_token_music(raw)
    if not data:
        err_msg = f"ERROR: Stage3 Token解析失败。AI返回内容:\n{raw[:500]}"
        print(f"[MusicComposer] {err_msg}")
        return {"error": err_msg}
    print(f"[MusicComposer] Stage3 完成: {len(data['sections'])}段, "
          f"duration={data.get('duration_sec','?')}s, title={data.get('title','?')}")
    return data


# ==================== 渲染引擎 ====================

def _parse_bar_notes(bar_str, beat_dur):
    """解析紧凑格式的小节音符: 'C4q E4q G4q C5h' """
    events = []
    current_beat = 0.0
    if not bar_str or bar_str in ("-", "-w", "r", "rest"):
        return events
    for token in bar_str.strip().split():
        result = _parse_note_compact(token)
        if result is not None:
            midis, dur_beats = result
            events.append((current_beat, midis, dur_beats * beat_dur))
            current_beat += dur_beats
    return events


def _parse_bar_drums(bar_str, beat_positions=4):
    """解析紧凑格式鼓: 'k h s h' """
    events = []
    words = bar_str.strip().split()
    for i, w in enumerate(words[:beat_positions]):
        w = w.strip().lower()
        if w in ("-", "", "rest"):
            continue
        notes = []
        for d in w.split("+"):
            drum_name = COMPACT_DRUM_MAP.get(d, d)
            n = DRUM_NOTES.get(drum_name)
            if n:
                notes.append(n)
        if notes:
            events.append((float(i), notes))
    return events


def _render_to_audio(music_data, wav_path):
    """将音乐数据渲染为 WAV 音频文件"""
    try:
        if isinstance(music_data, dict) and "error" in music_data:
            return f"ERROR: 无法渲染音频，因为音乐数据生成失败: {music_data['error']}"

        bpm = music_data.get("bpm", 120)
        time_sig = music_data.get("time", [4, 4])
        bpb = time_sig[0] if isinstance(time_sig, (list, tuple)) and len(time_sig) > 0 else 4
        beat_dur = 60.0 / bpm
        bar_dur = beat_dur * bpb
        instruments = music_data.get("instruments", {})
        sections = music_data.get("sections", [])

        if not instruments:
            return "ERROR: 音乐数据中缺少 instruments 字段，无法渲染。"
        if not sections:
            return "ERROR: 音乐数据中缺少 sections 字段，无法渲染。"

        max_total = sum(s.get("bars", 4) * bar_dur for s in sections) + 10.0
        total_samp = int(max_total * SAMPLE_RATE)
        audio = np.zeros(total_samp, dtype=np.float64)
        _reset_humanize_seed()

        swing = music_data.get("swing", 0.0)
        if swing > 0:
            print(f"[MusicComposer] 应用Swing: {swing:.0%}")

        section_start = 0.0
        crossfade_samples = int(0.02 * SAMPLE_RATE)
        prev_section_end = 0

        print(f"[MusicComposer] 开始渲染 {len(sections)} 个段落...")
        for si, section in enumerate(sections):
            bars = section.get("bars", 4)
            energy = section.get("energy", 0.5)
            tracks = section.get("tracks", {})
            chords = section.get("chords", [])
            sec_vol = 0.6 + energy * 0.4
            max_bar_end = 0.0
            sec_start_samp = int(section_start * SAMPLE_RATE)

            chord_midi_notes = []
            current_chord_idx = 0

            for inst_name, inst_type in instruments.items():
                if inst_name not in tracks:
                    continue
                is_melodic = inst_type not in ("drums", "bass")
                td = tracks[inst_name]
                bar_items = td if isinstance(td, list) else [td]

                if inst_type == "drums":
                    for bar_idx, bar_item in enumerate(bar_items):
                        if bar_idx >= bars:
                            break
                        drum_ev = _parse_bar_drums(str(bar_item), bpb)
                        for beat_pos, drum_notes in drum_ev:
                            abs_time = section_start + (bar_idx * bpb + beat_pos) * beat_dur
                            abs_time += _humanize_time(2)
                            for dn in drum_notes:
                                ds = int(beat_dur * SAMPLE_RATE * 0.8)
                                ss = int(abs_time * SAMPLE_RATE)
                                if ss + ds <= total_samp and ds > 0:
                                    dw = _synth_drum(dn, beat_dur)
                                    if len(dw) > 0:
                                        end = min(ss + len(dw), total_samp)
                                        audio[ss:end] += dw[:end - ss] * sec_vol * (0.7 + energy * 0.3)
                        max_bar_end = max(max_bar_end, (bar_idx + 1) * bpb)
                else:
                    synth_fn = INSTRUMENT_SYNTH.get(inst_type, _synth_piano)
                    if synth_fn is None:
                        synth_fn = _synth_piano
                    for bar_idx, bar_item in enumerate(bar_items):
                        if bar_idx >= bars:
                            break
                        if bar_idx < len(chords) and chords[bar_idx]:
                            chord_midi_notes = _chord_to_midi_notes(chords[bar_idx])
                        note_ev = _parse_bar_notes(str(bar_item), bar_dur / bpb)
                        for start_beat, midi_notes, dur_beats in note_ev:
                            beat_pos = bar_idx * bpb + start_beat
                            if is_melodic and swing > 0:
                                frac = beat_pos % 1.0
                                if 0.15 < frac < 0.85:
                                    beat_pos += swing * 0.5
                            abs_start = section_start + beat_pos * beat_dur
                            abs_start += _humanize_time(3)
                            ns = int(dur_beats * SAMPLE_RATE)
                            ss = int(abs_start * SAMPLE_RATE)
                            if ns <= 0 or ss >= total_samp:
                                continue
                            if ss + ns > total_samp:
                                ns = total_samp - ss
                            for mn in midi_notes:
                                if is_melodic and chord_midi_notes:
                                    mn = _correct_note_to_chord(mn, chord_midi_notes)
                                freq = _midi_to_freq(mn)
                                vel = _humanize_vel(int(70 + energy * 40))
                                wave = synth_fn(freq, ns, vel)
                                audio[ss:ss + ns] += wave / max(len(midi_notes), 1) * sec_vol
                        max_bar_end = max(max_bar_end, (bar_idx + 1) * bpb)

            actual_dur = max_bar_end * beat_dur + beat_dur * 0.25
            declared_dur = bars * bar_dur
            advance = max(actual_dur, declared_dur)
            if declared_dur - actual_dur > bar_dur:
                print(f"[MusicComposer] 段落'{section.get('name','?')}' 声明{bars}小节，"
                      f"实际内容仅{max_bar_end:.1f}拍，自动缩短间距")
                advance = actual_dur + beat_dur * 0.5

            next_start = section_start + advance
            next_start_samp = int(next_start * SAMPLE_RATE)
            if si > 0 and crossfade_samples > 0:
                fade_start = max(sec_start_samp, prev_section_end - crossfade_samples)
                fade_end = min(sec_start_samp + crossfade_samples, total_samp)
                if fade_end > fade_start:
                    fade_len = fade_end - fade_start
                    cross_env = np.linspace(0, 1, fade_len)
                    if fade_start < len(audio) and fade_end <= len(audio):
                        audio[fade_start:fade_end] *= cross_env

            prev_section_end = next_start_samp
            section_start = next_start

        fx_mx = np.max(np.abs(audio))
        if fx_mx > 0:
            audio = audio / fx_mx * 0.85
        final_samp = int(section_start * SAMPLE_RATE) + int(2.0 * SAMPLE_RATE)
        audio = audio[:final_samp]
        total_samp = final_samp

        effects = music_data.get("effects", {})
        reverb_wet = effects.get("reverb", 0.0)
        delay_wet = effects.get("delay", 0.0)
        delay_beats = effects.get("delay_beats", 3)
        feedback = effects.get("feedback", 0.35)
        lowcut = effects.get("lowcut", 0)
        highcut = effects.get("highcut", 0)

        if reverb_wet > 0:
            print(f"[MusicComposer] 应用混响: wet={reverb_wet:.1f}")
            audio = _apply_reverb(audio, wet=reverb_wet, room_size=0.5)
        if delay_wet > 0:
            print(f"[MusicComposer] 应用延迟: wet={delay_wet:.1f} beats={delay_beats}")
            audio = _apply_delay(audio, wet=delay_wet, delay_beats=delay_beats,
                                 feedback=feedback, bpm=bpm)
        if lowcut > 0 or (highcut > 0 and highcut < 20000):
            print(f"[MusicComposer] 应用EQ: lowcut={lowcut}Hz highcut={highcut}Hz")
            audio = _apply_eq(audio, lowcut=lowcut, highcut=highcut)

        print(f"[MusicComposer] 应用立体声宽度")
        audio = _apply_stereo_width(audio, width=0.5)
        print(f"[MusicComposer] 应用温暖度")
        audio = _apply_warmth(audio, amount=0.06)

        fade = min(int(2.0 * SAMPLE_RATE), total_samp // 15)
        if fade > 0:
            audio[:fade] *= np.linspace(0, 1, fade)
            audio[-fade:] *= np.linspace(1, 0, fade)

        efx_mx = np.max(np.abs(audio))
        if efx_mx > 1.0:
            audio = audio / efx_mx * 0.95

        a16 = (np.clip(audio, -1, 1) * 32767).astype(np.int16)

        output_dir = os.path.dirname(wav_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        with open(wav_path, "wb") as f:
            ds = a16.nbytes
            channels = 2 if a16.ndim > 1 else 1
            f.write(b"RIFF"); f.write(struct.pack("<I", 36 + ds)); f.write(b"WAVE")
            f.write(b"fmt "); f.write(struct.pack("<I", 16)); f.write(struct.pack("<H", 1))
            f.write(struct.pack("<H", channels)); f.write(struct.pack("<I", SAMPLE_RATE))
            f.write(struct.pack("<I", SAMPLE_RATE * channels * 2)); f.write(struct.pack("<H", channels * 2))
            f.write(struct.pack("<H", 16)); f.write(b"data"); f.write(struct.pack("<I", ds))
            a16.tofile(f)
        print(f"[MusicComposer] 渲染完成: {section_start:.1f}s, {len(a16)/SAMPLE_RATE:.1f}s音频")
        return wav_path
    except Exception as e:
        err_msg = f"ERROR: 音频渲染失败: {e}"
        print(f"[MusicComposer] {err_msg}")
        traceback.print_exc()
        return err_msg


def _write_midi(music_data, midi_path):
    """将音乐数据写入 MIDI 文件"""
    try:
        if isinstance(music_data, dict) and "error" in music_data:
            return f"ERROR: 无法写入MIDI，因为音乐数据生成失败: {music_data['error']}"

        bpm = music_data.get("bpm", 120)
        time_sig = music_data.get("time", [4, 4])
        bpb = time_sig[0] if isinstance(time_sig, (list, tuple)) and len(time_sig) > 0 else 4
        beat_dur = 60.0 / bpm
        bar_dur = beat_dur * bpb
        instruments = music_data.get("instruments", {})
        sections = music_data.get("sections", [])

        if not instruments:
            return "ERROR: 音乐数据中缺少 instruments 字段，无法生成MIDI。"
        if not sections:
            return "ERROR: 音乐数据中缺少 sections 字段，无法生成MIDI。"

        def sec2tick(sec):
            return int(sec * bpm / 60.0 * TICKS_PER_BEAT)

        def vlv(v):
            buf = bytearray()
            while True:
                b = v & 0x7F; v >>= 7
                buf.append(b | 0x80 if v else b)
                if not v:
                    break
            return bytes(buf)

        def i32(v):
            return struct.pack(">I", v)

        def i16(v):
            return struct.pack(">h", v)

        def i24(v):
            return struct.pack(">I", v)[1:]

        def non(ch, n, v):
            return bytes([0x90 | ch, n, v])

        def noff(ch, n):
            return bytes([0x80 | ch, n, 0])

        def pc(ch, prog):
            return bytes([0xC0 | ch, prog])

        all_ev = []
        ch_map = {}
        nc = 0
        section_start = 0.0

        def energy_vel(energy):
            return int(50 + energy * 60)

        for section in sections:
            bars = section.get("bars", 4)
            energy = section.get("energy", 0.5)
            vel = energy_vel(energy)
            tracks = section.get("tracks", {})
            max_bar_end = 0.0

            for inst_name, inst_type in instruments.items():
                if inst_name not in tracks:
                    continue
                if inst_type not in ch_map:
                    if inst_type == "drums":
                        ch_map[inst_type] = 9
                    else:
                        ch_map[inst_type] = nc
                        nc += 1
                        if nc == 9:
                            nc = 10
                ch = ch_map[inst_type]
                td = tracks[inst_name]
                bar_items = td if isinstance(td, list) else [td]

                if inst_type == "drums":
                    for bar_idx, bar_item in enumerate(bar_items):
                        if bar_idx >= bars:
                            break
                        drum_ev = _parse_bar_drums(str(bar_item), bpb)
                        for beat_pos, drum_notes in drum_ev:
                            t = section_start + (bar_idx * bpb + beat_pos) * beat_dur
                            tick = sec2tick(t)
                            for dn in drum_notes:
                                all_ev.append((tick, non(ch, dn, 100)))
                        max_bar_end = max(max_bar_end, (bar_idx + 1) * bpb)
                else:
                    for bar_idx, bar_item in enumerate(bar_items):
                        if bar_idx >= bars:
                            break
                        note_ev = _parse_bar_notes(str(bar_item), bar_dur / bpb)
                        for start_beat, midi_notes, dur_beats in note_ev:
                            t_s = section_start + (bar_idx * bpb + start_beat) * beat_dur
                            t_e = t_s + dur_beats
                            ts = sec2tick(t_s)
                            te = sec2tick(t_e)
                            for mn in midi_notes:
                                all_ev.append((ts, non(ch, mn, vel)))
                                all_ev.append((te, noff(ch, mn)))
                        max_bar_end = max(max_bar_end, (bar_idx + 1) * bpb)

            advance = max(max_bar_end * beat_dur + beat_dur * 0.25, bars * bar_dur)
            if bars * bar_dur - max_bar_end * beat_dur > bar_dur:
                advance = max_bar_end * beat_dur + beat_dur * 0.5
            section_start += advance

        setup = []
        for it, ch in ch_map.items():
            if it != "drums":
                prog = GM_INSTRUMENTS.get(it, 0)
                setup.append((0, pc(ch, prog)))

        track_ev = setup + sorted(all_ev, key=lambda x: x[0])

        data = bytearray()
        data.extend(bytes([0x00, 0xFF, 0x03, 5]) + b"music")
        data.extend(bytes([0x00, 0xFF, 0x51, 0x03]) + i24(int(60000000 / bpm)))
        data.extend(bytes([0x00, 0xFF, 0x58, 0x04]) + bytes([time_sig[0], 2, 24, 8]))
        prev = 0
        for tick, msg in track_ev:
            delta = tick - prev
            prev = tick
            data.extend(vlv(delta))
            data.extend(msg)
        data.extend(vlv(0))
        data.extend(bytes([0xFF, 0x2F, 0x00]))

        output_dir = os.path.dirname(midi_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        with open(midi_path, "wb") as f:
            f.write(b"MThd"); f.write(i32(6)); f.write(i16(0)); f.write(i16(1))
            f.write(i16(TICKS_PER_BEAT)); f.write(b"MTrk"); f.write(i32(len(data)))
            f.write(data)
        return midi_path
    except Exception as e:
        err_msg = f"ERROR: MIDI 生成失败: {e}"
        print(f"[MusicComposer] {err_msg}")
        traceback.print_exc()
        return err_msg


def _cleanup_old_temps(output_dir, keep=5):
    """清理旧的临时 WAV/MIDI 文件，只保留最近 N 个"""
    try:
        temps = []
        for f in os.listdir(output_dir):
            fp = os.path.join(output_dir, f)
            if os.path.isfile(fp) and any(f.startswith(p) for p in ("compose_",)):
                temps.append((os.path.getmtime(fp), fp))
        temps.sort(reverse=True)
        for _, fp in temps[keep:]:
            try:
                os.remove(fp)
                print(f"[MusicComposer] 清理临时文件: {os.path.basename(fp)}")
            except:
                pass
    except Exception:
        pass


def _to_mp3(wav, mp3):
    """将 WAV 转换为 MP3，需要 pydub + ffmpeg"""
    try:
        from pydub import AudioSegment
    except ImportError:
        print(f"[MusicComposer] 警告: pydub 未安装，无法转换为 MP3，将返回 WAV 文件。\n"
              f"如需 MP3 格式，请执行: pip install pydub")
        return wav
    try:
        AudioSegment.from_wav(wav).export(mp3, format="mp3", bitrate="192k")
        print(f"[MusicComposer] MP3: {mp3}")
        return mp3
    except FileNotFoundError as e:
        print(f"[MusicComposer] MP3 转换失败: 找不到 ffmpeg。\n"
              f"请安装 ffmpeg 并将其加入系统 PATH：\n"
              f"  1. 下载: https://www.gyan.dev/ffmpeg/builds/ (选 ffmpeg-release-essentials.zip)\n"
              f"  2. 解压后将 bin 目录加入 PATH 环境变量\n"
              f"  3. 或使用: choco install ffmpeg / winget install ffmpeg\n"
              f"当前将返回 WAV 文件作为替代。")
        return wav
    except Exception as e:
        print(f"[MusicComposer] MP3 转换失败: {e}，将返回 WAV 文件。")
        traceback.print_exc()
        return wav


# ==================== 主入口 ====================

def compose_music(prompt, duration=180, key="C", bpm=None):
    """
    AI 作曲 V4 - 三阶段流水线
    Stage1: 主旋律创作 → Stage2: 编曲展开 → Stage3: 完整拼装 → 渲染 → MP3

    Args:
        prompt: 作曲需求描述
        duration: 目标时长(秒)，默认180(3分钟)
        key: 调性
        bpm: 速度(可选)

    Returns:
        成功: MP3/WAV 文件路径
        失败: "ERROR: 错误信息" 字符串
    """
    # ====== 前置检查 ======
    dep_errors = _check_dependencies()
    if dep_errors:
        return f"ERROR: 依赖检查失败:\n" + "\n".join(dep_errors)

    if not prompt or not isinstance(prompt, str):
        return "ERROR: prompt 参数不能为空，请提供音乐创作需求描述。"

    if duration <= 0 or duration > 600:
        return f"ERROR: duration 参数无效 ({duration})。请设置在 1-600 秒之间。"

    output_dir = "./downloads/generated_videos"
    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        return f"ERROR: 无法创建输出目录 {output_dir}: {e}"

    stem = f"compose_{int(time.time() * 1000)}"

    # ====== Stage 1: 主旋律 ======
    motif = _stage1_compose_melody(prompt, key, duration)
    if isinstance(motif, dict) and "error" in motif:
        return f"ERROR: Stage1 主旋律创作失败。\n{motif['error']}"
    if not motif:
        return "ERROR: Stage1 主旋律创作失败（返回空数据）。"

    # ====== Stage 2: 编曲 ======
    arrangement = _stage2_develop_arrangement(motif, prompt, duration)
    if isinstance(arrangement, dict) and "error" in arrangement:
        return f"ERROR: Stage2 编曲展开失败。\n{arrangement['error']}"
    if not arrangement:
        return "ERROR: Stage2 编曲展开失败（返回空数据）。"

    # ====== Stage 3: 拼装 ======
    full_song = _stage3_assemble_song(arrangement, prompt, duration)
    if isinstance(full_song, dict) and "error" in full_song:
        return f"ERROR: Stage3 完整拼装失败。\n{full_song['error']}"
    if not full_song:
        return "ERROR: Stage3 完整拼装失败（返回空数据）。"

    # 确保BPM/key从初始motif传递
    if "bpm" not in full_song or not full_song.get("bpm"):
        full_song["bpm"] = motif.get("bpm", 120)
    if "key" not in full_song or not full_song.get("key"):
        full_song["key"] = key

    print(f"[MusicComposer] 三阶段完成，开始渲染...")

    # ====== MIDI ======
    midi_path = os.path.join(output_dir, f"{stem}.mid")
    midi_result = _write_midi(full_song, midi_path)
    if isinstance(midi_result, str) and midi_result.startswith("ERROR:"):
        print(f"[MusicComposer] MIDI生成失败: {midi_result}")
    else:
        print(f"[MusicComposer] MIDI: {midi_path}")

    # ====== 渲染 WAV ======
    wav_path = os.path.join(output_dir, f"{stem}.wav")
    wav_result = _render_to_audio(full_song, wav_path)
    if isinstance(wav_result, str) and wav_result.startswith("ERROR:"):
        return f"ERROR: 音频渲染失败。\n{wav_result}"

    if not os.path.exists(wav_path):
        return f"ERROR: WAV 文件未生成: {wav_path}"

    print(f"[MusicComposer] WAV: {wav_path} ({os.path.getsize(wav_path)/1024:.0f}KB)")

    # ====== 清理过期临时文件（保留5条以内的旧文件） ======
    _cleanup_old_temps(output_dir, keep=5)

    # ====== MP3 ======
    mp3_path = os.path.join(output_dir, f"{stem}.mp3")
    result = _to_mp3(wav_path, mp3_path)
    if result == wav_path:
        # MP3 转换失败或 pydub 未安装，返回 WAV
        return wav_path

    if os.path.exists(result):
        try:
            os.remove(wav_path)
        except:
            pass
        return result

    return wav_path


if __name__ == "__main__":
    r = compose_music("温馨治愈的钢琴曲，C大调，久石让风格", duration=60, key="C")
    print(f"结果: {r}")
