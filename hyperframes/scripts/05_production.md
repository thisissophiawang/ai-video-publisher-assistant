# 05 Production

## 制作目标

制作一条 12 秒、720 x 1280、9:16 竖屏短视频。

该视频不是单张 LinkedIn 截图动效，而是由多个镜头组成：

```text
纽约市 skyline 开场背景
哥伦比亚大学校园 / 毕业生氛围
留学生求职场景
LinkedIn 主页优化
JD 分析与简历关键词
英文面试模拟
AI 求职帮助 CTA
```

## 文件落点规则

所有 HyperFrames 相关文件必须放在：

```text
hyperframes/
```

不得把素材、脚本、音频、字幕、成片散落到其他目录。

## 素材路径

参考图：

```text
hyperframes/assets/input/reference_linkedin_style.jpg
hyperframes/assets/input/reference_nyc_skyline.jpg
hyperframes/assets/input/reference_columbia_graduation.jpg
```

参考图使用规则：

```text
reference_nyc_skyline.jpg：
用于开场、转场、结尾 CTA 背景，建立纽约城市环境。

reference_columbia_graduation.jpg：
用于哥大校园/毕业生氛围参考，建立目标观众身份感。

reference_linkedin_style.jpg：
只用于 LinkedIn 主页优化镜头，不得作为整条视频唯一画面。
```

图片素材：

```text
hyperframes/assets/images/
```

视频素材：

```text
hyperframes/assets/video/
```

配音：

```text
hyperframes/assets/audio/
```

字幕：

```text
hyperframes/assets/subtitles/
```

预览：

```text
hyperframes/renders/
```

最终导出：

```text
hyperframes/exports/
```

## 制作流程

```text
1. 根据 01_design.md 确认视觉风格和目标观众。
2. 根据 02_script.md 确认最终旁白和字幕。
3. 先制作纽约 skyline 和哥大校园背景资产。
4. 根据 03_storyboard.md 制作 5 个镜头。
5. 根据 04_voiceover.md 生成中文女生旁白。
6. 制作字幕文件，并保证字幕与旁白一致。
7. 合成视频、配音、字幕、背景音乐。
8. 导出 MP4 到 hyperframes/exports/。
9. 根据 06_validation.md 验收。
```

## 成片命名

```text
hyperframes/exports/study_abroad_ai_job_search_12s_720p.mp4
```

## 制作限制

```text
不要只用 LinkedIn 截图做完整视频。
不要只用纽约或哥大背景做空镜，必须结合 AI 求职流程。
不要出现真实个人信息。
不要使用未经授权的 logo、音乐或人像。
不要清晰展示未经授权的学校商标或校徽。
不要承诺 guaranteed offer、100% 找到工作、包就业。
不要让字幕遮挡脸部、按钮、简历标题或 CTA。
```
