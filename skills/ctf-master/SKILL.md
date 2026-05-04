---
name: ctf-master
description: CTF 综合入口 — 路由到 PWN / Crypto / Web / Reverse / Misc / SQLi 子技能。触发词：CTF、flag{xxx}、ctf-wiki、解题流程、pwn/逆向/密码/web/杂项
version: 1.0
tags: [ctf, hacking, ctf-wiki, google-ctf, awesome-ctf]
---

# CTF Master — 综合入口

四源融合：
- **ctf-wiki**（`~/ctf-wiki/docs/zh/docs/`）— 14 方向完整理论，glibc 深度，攻防原理
- **google-ctf**（`~/google-ctf/`）— 2017-2025 真实 challenge，Dockerfile + challenge.yaml 格式
- **awesome-ctf**（`~/awesome-ctf/`）— 工具链清单，平台索引，写题技巧
- **ctf-skills**（`~/ctf-skills/`）— 决策树 + 可运行脚本模板

## 决策树

```
看到 CTF 题 / flag{xxx}
├── 题目给了 binary → 逆向 / PWN
│   ├── 有源码（*.c）→ 分析逻辑 + 漏洞定位
│   ├── 无源码 → ghidra/IDA 分析 + pwntools 调试
│   ├── 题型：栈溢出/ROP/Heap → ctf-pwn
│   └── 题型：算法混淆/壳/反调试 → ctf-reverse
├── 题目是编码/加密/哈希 → ctf-crypto-comprehensive
│   ├── 古典（摩斯/凯撒/栅栏）→ ctf-skills esoteric_decoder.py
│   └── 现代（RSA/AES/ECC）→ ctf-wiki crypto 深度分析
├── 题目是 Web 流量/URL/API → ctf-web
│   ├── SQL 注入 → ctf-sqli
│   ├── SSRF/XXE/CSRF → ctf-wiki web/
│   └── JS 源码分析 → ctf-wiki web/javascript/
├── 题目是图片/音频/流量/内存dump → ctf-misc
│   ├── 隐写 → ctf-stego
│   ├── 取证 → ctf-wiki misc/
│   └── OSINT → google-ctf misc 类题目
└── 不确定 → 先读 ctf-wiki 导航页 ~/ctf-wiki/docs/zh/docs/
```

## 各方向入口

| 方向 | 触发词 | 参考来源 |
|------|--------|---------|
| **ctf-pwn** | PWN、栈溢出、ROP、格式化字符串、UAF、tcache、House of 系列 | ctf-wiki pwn/（ptmalloc2/tcache/unlink/House-of×7） |
| **ctf-crypto-comprehensive** | 密码学题、base64/hex、RSA/AES 破解、古典密码、哈希长度扩展 | ctf-skills 模板 + ctf-wiki crypto/ |
| **ctf-reverse** | 逆向、IDA、GHIDRA、Frida、反混淆、壳、脱壳 | ctf-wiki reverse/ + awesome-ctf 工具链 |
| **ctf-web** | Web、SQL 注入、XSS、SSRF、文件上传、HTTP | ctf-wiki web/ + awesome-ctf tools |
| **ctf-misc** | 取证、流量分析、图片隐写、OSINT、内存分析 | ctf-wiki misc/ + google-ctf misc |
| **ctf-sqli** | SQLMap、报错注入、布尔盲注、时间盲注、堆叠注入、宽字节 | ctf-wiki web/sqli/ |

## Google CTF 题目格式

每道题目录下有：
- `challenge.yaml` — 元数据（flag 格式、难度、category）
- `challenge/` — 题目文件（Dockerfile 启动靶场）
- `solves/` — 官方解法（参考价值高）

快速定位某年某方向：
```bash
ls ~/google-ctf/ctf-{year}/{quals,beginners,hackceler8}/ | grep -i pwn
```

## CTF-Wiki 导航

```
~/ctf-wiki/docs/zh/docs/
├── crypto/          # 密码学（RSA/ECC/AEAD/LCG/PRNG/哈希）
├── pwn/             # PWN（栈/堆/格式化字符串/House of）
├── web/             # Web（SQL/XSS/SSRF/反序列化/内网）
├── reverse/         # 逆向（语言/混淆/识别）
├── misc/            # 杂项（取证/流量/OSINT/隐写）
├── blockchain/      # 区块链
└── android/         # Android
```

## 常用工具速查

| 工具 | 用途 | 来源 |
|------|------|------|
| pwntools | PWN 脚本 | `~/ctf-skills/ctf-pwn/solver.py` 模板 |
| Ghidra | 逆向分析 | awesome-ctf tools |
| RSACTFTool | RSA 攻击 | ctf-wiki crypto/asymmetric/rsa/ |
| CyberChef | 编码/加密快速尝试 | awesome-ctf platforms |
| sqlmap | SQL 注入自动化 | ctf-sqli |
| zsteg/steghide | 图片隐写 | ctf-misc |

## 注意事项

- google-ctf 靶场含**故意植入的漏洞**，绝不在生产环境运行 challenge 二进制文件
- 题目 Docker 环境：`cd ~/google-ctf/ctf-{year}/ && docker compose up`
- CTF-Wiki 的 crypto/pwn 目录有独家深度内容（ptmalloc2 原理、House of 系列 7 种完整利用链）
