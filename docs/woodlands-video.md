# Woodlands 五分钟以内实际汇报示例

这个示例把已完成的交互 HTML 组织成连续汇报：英文女声说明设计逻辑，真实录制模型旋转、方案切换、功能联读和原册浏览，再加入原创轻音乐与同步字幕。它是已导出的影片；技能本身是一套可复用的制作流程和输入要求。

- [横屏 MP4](https://github.com/u20260608744-glitch/-HTML-/releases/download/v1.1.0/woodlands-landscape-1080p.mp4)：1920×1080。
- [竖屏 MP4](https://github.com/u20260608744-glitch/-HTML-/releases/download/v1.1.0/woodlands-portrait-1080p.mp4)：1080×1920，另做手机构图。
- [发布下载 ZIP](https://github.com/u20260608744-glitch/-HTML-/releases/download/v1.1.0/woodlands-social-downloads.zip)：两版视频、两张封面、发布使用说明。
- [英文讲稿](video/narration-en.md)、[字幕 SRT](video/woodlands-en.srt)、[章节索引](video/chapter-times.md)、[音乐来源](video/music-provenance.md)、[验收摘要](video/verification-summary.json)。

![实际横屏影片封面](images/woodlands-video-cover.jpg)

## 内容及时间

| 开始时间 | 汇报内容 |
|---|---|
| 00:00 | 项目任务、三个花园方向与实际模型旋转 |
| 00:22 | 场地、交通、配套和周边尺度 |
| 00:50 | 城市联系与花园社区的设计回应 |
| 01:09 | 三种形体的空间关系与取舍 |
| 01:35 | 各方案总图、共同任务与面积指标 |
| 02:27 | 剖面中的上下空间组织 |
| 02:46 | 住宅、配套、景观、水景与到达五类空间 |
| 03:21 | 三个已建住宅案例及可借鉴机制 |
| 03:48 | 同口径比较与后续设计重点 |
| 04:14 | 原册快速浏览与证据回看 |
| 04:33 | 设计决策与结束 |

母版295.000秒，发布版容器295.019秒；最后音频编码包造成约0.019秒差异，两版都低于300秒。25fps、7375帧，H.264视频、AAC音频、yuv420p、SAR1:1、MP4索引在媒体数据之前，可用于常见播放器。具体平台或账号是否接受上传未执行验证。

模型运动采用实录的正常速度，可从真实录制帧延长停留。旁白使用英文女声 `en-GB-SoniaNeural`；字幕根据实测声音对齐。背景器乐由合成制作流程原创生成，出处与使用说明单独保留。原册17页采用快速浏览，不等于逐页详细讲解。本案例的三方案、17页、11段、75镜头不是新项目的固定条件。

## 版本边界

影片记录的 HTML 快照 SHA256：

`9998461e3f047e27841eab5166067331b3ea39cfef14146d4507e7ecefff18bb`

之后修复了 HTML 在部分视口下功能说明文字的重叠，2026-10-03 当前成品 SHA256：

`0739518696654ca25a1c03fa02af89a98803e64c183f4e6fdbd9db601fad2b3f`

因此，这份影片属于录制时的快照；不能称已经重新录制上述修订。修订未改变建筑几何与指标，但新版 HTML 与旧片的版本应分别追溯。后续项目改动图面、语义或讲稿时，重录受影响章节并重新核验字幕、横竖导出和下载包。

## 下载文件校验

| Release 文件名 | SHA256 |
|---|---|
| `woodlands-landscape-1080p.mp4` | `36f9045d1baae777f2aeb1a89fd1e1f4ace5874f92511aa6459fc8095ea26443` |
| `woodlands-portrait-1080p.mp4` | `f747de09caed0a51aa2116c3fdded8c20f6ce6dceafa40151a9422ab0f25a789` |
| `woodlands-social-downloads.zip` | `74236f8e40bf09d27f7083024a82dd4d8bf64f8548c75756cab797ff8d11cc83` |

附件使用简洁英文文件名，内容与已交付版本相同。本仓库已公开，已发布的视频与下载包可直接下载。这个视频可作为理解技能效果的案例；新项目必须使用自己的真实图纸、模型、统计与获准素材。
