## 📁 MEMORY — Hermes Agent Persistent Memory
## 格式：每条记忆以 § 分隔；[标签] 标注分类；末尾注过期时间

══════════════════════════════════════════════
## 🖥️ 环境配置 [ENV] · 2026-04-19
══════════════════════════════════════════════
§
[ENV · 永久] 工作目录：/Users/can/.hermes/hermes-agent（所有文件读写只能在此）
§
[ENV · 永久] MiniMax API：Token Plan Key（sk-cp-...）Base URL=https://api.minimaxi.com/anthropic；普通 key/SimpleMem=https://api.minimaxi.com/v1
§
§
[ENV · 2026-04-29] Token Plan key (sk-cp-...) 已验证可用：abab6.5s-chat 和 MiniMax-M2.7 可用；MiniMax-Text-01（非 mini）返回 403。config.yaml minimax-cn provider 使用 SkillClaw relay (localhost:30000)，不直连。
§
§
[USER · 永久] 用户名：r00tcc（飞书平台）
§
[USER · 永久] 沟通偏好：中文；简洁直接；不喜欢废话
§
[USER · 永久] 每天结束前必须 commit 所有改动，不留任何遗留工作。
§
[USER · 永久] 工作风格：分析后立即 full implementation；完整流程：分析→测试→安装→回归测试→上线；偏好系统性落地；每天结束前 commit
§
[SECURITY · 2026-04-29] git 仓库敏感信息审计：先用 `git log origin/main..HEAD` 扫 unpushed commits；用 `git log --all -S "sk-" --oneline` 搜历史（比 grep 快）；`.gitignore` 确保 `evolver/` 等含真实 key 的 .env 目录被排除；测试文件中的 `ghp_xx...xxxx` 类是占位符，非泄露；skills-quality 会误判 git 读取命令为 dangerous，skill 创建会被 block
§
[ENV · 2026-04-29] SkillClaw 仅有 /v1/models 端点（返回 {"id":"MiniMax-M2.7"}），无 admin/debug/health 端点
§
[ENV · 2026-05-01] skills/ gitlink→普通目录已修复；push 408网络问题；skills/新增3个security skill(Hack-with-Github/Awesome-Hacking)
§
[COZE] MySQL coze-mysql/opencoze/coze/coze123；PAT: workflow/run✓ list✗
§
[CAVEMAN · 2026-05-03] hermes-agent caveman skill(cb219f96)：输出/输入双压缩，强度lite/full/ultra/wenyan-lite/wenyan/wenyan-ultra，配置~/.config/caveman/config.json
§
§
[CTF · 2026-05-04] CTF体系融合4仓+入口skill：
  ①~/ctf-wiki/ (14方向理论) ②~/google-ctf/ (2017-2025真实challenge)
  ③~/awesome-ctf/ (工具链) ④~/ctf-skills/ (脚本模板)
  4个skill已push到hermes-agent: ctf-master(入口), ctf-pwn(ROP/fmtstr/tcache/House-of×7),
  ctf-crypto-comprehensive(RSACTFTool/Coppersmith/AES), ctf-skills-toolkit(实测脚本)
§
[CTF · 2026-05-04] ctf-wiki pwn独家:ROP(basic+medium+fancy=1133行)/ptmalloc2(★tcache=2459行,unlink=1431行)/fmtstr(823行)/House-of×7/UAF/IntegerOverflow
§
[CTF · 2026-05-04] CTF crypto工具:RSACTFTool/XORTool/QuipQuip/CyberChef; crypto深度:coppersmith/rsa_module(641行)/hash碰撞/LLL格基
§
[CTF · 2026-05-04] misc工具:Wireshark/volatility3/steghide/zsteg/AperiSolve; misc取证:archive/disk-memory/traffic/recon