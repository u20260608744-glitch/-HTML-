# Woodlands 5分钟版原创配乐

本音轨由 Codex 使用既有原创和声、旋律动机及数学音色算法，为本项目重新合成 300 秒。音乐包含柔和电钢、暖 Pad 与疏朗旋律，约 64 BPM。未下载第三方音乐，未使用现有录音、采样乐器、歌词或人声。

文件：`audio/woodlands-original-score.wav`；精确时长 300 秒，48 kHz、双声道、16-bit PCM，14,400,000 个音频帧。开头约 4 秒渐入，结尾约 9 秒渐出。438 个音符事件（224 电钢伴奏、54 旋律、160 Pad），40 次和声推进，18 个音高。

整段测量：−23.00 LUFS，真峰值 −11.64 dBTP，RMS −25.05 dBFS，零削波；首尾帧均为数字零。使用 FFmpeg 7.1 测量并施加 +3.80 dB 固定增益，保留动态。完整记录见 `audio/woodlands-original-score.metrics.json`。

这是独立配乐。短片混音应以英文女声为主，并在旁白时用侧链压低配乐。最终影片不得超过 300 秒；若实际片长较短，截取所需时长，并在实际片尾重新施加渐出，勿仅依赖本文件 300 秒处的渐出。

生成脚本：`C:/Users/jxjfe/Documents/ChatGPT/PPT优化/output/woodlands-video/tools/compose_score.py`。参数：`--duration 300 --output E:/人工智能/Codex/10/Woodlands_汇报视频/5分钟版/audio/woodlands-original-score.wav`，随机种子 641003。生成时采用短 float32 块，全部临时音频在本 E 盘目录，完成后已清除。原长版视频、配乐和 HTML 没有修改。

音频 SHA256：`d050c0b6bb76b059a1d834261f29f7c0aa044276037eb8a8c16e828857ee2348`。
