---
name: ctf-skills-toolkit
description: CTF 工具包 — ctf-skills 实测脚本入口（crypto_toolkit.py/esoteric_decoder.py/TEA/XTEA/RC4）+ ctf-wiki/awesome-ctf/google-ctf 交叉索引
version: 1.0
tags: [ctf, tools, python, scripting, decoder]
---

# CTF Skills Toolkit — 工具包入口

参考来源：
- **ctf-skills**（`~/ctf-skills/`）— 6 方向 SKILL.md + 实测脚本
- **awesome-ctf**（`~/awesome-ctf/`）— 工具链完整清单

## 实测脚本

| 脚本 | 位置 | 验证状态 |
|------|------|---------|
| crypto_toolkit.py | `~/ctf-skills/ctf-crypto/crypto_toolkit.py` | ✅ base64→flag{test} |
| esoteric_decoder.py | `~/ctf-skills/ctf-crypto/esoteric_decoder.py` | ✅ Morse/Binary/Brainfuck |
| TEA/XTEA | `~/ctf-skills/ctf-crypto/tea.py` | ✅ 实测可用 |
| solver.py (PWN模板) | `~/ctf-skills/ctf-pwn/solver.py` | 模板未实测 |
| Hash Length Extension | `hashpumpy` pip 包 | 需 `pip install hashpumpy` |

## 快速使用

```bash
# 编码/解码
python3 ~/ctf-skills/ctf-crypto/crypto_toolkit.py --encode base64 --input "flag{test}"
python3 ~/ctf-skills/ctf-crypto/crypto_toolkit.py --decode hex --input "666c6167"

# 古典密码
python3 ~/ctf-skills/ctf-crypto/esoteric_decoder.py -i morse -e ".- -... -.-."
python3 ~/ctf-skills/ctf-crypto/esoteric_decoder.py -i brainfuck -e ",+[-.,+]"

# XOR
python3 ~/ctf-skills/ctf-crypto/crypto_toolkit.py --xor-cipher <(echo -n "key") --input "ciphertext_hex"
```

## 路由表

```
需要工具时 → 根据题目类型选：
├── 密码学脚本 → ctf-crypto-comprehensive
├── PWN 模板 → ctf-pwn
├── 逆向工具 → ctf-reverse（awesome-ctf tools）
├── Web 工具 → ctf-web（sqlmap/dirb/gobuster）
└── 取证工具 → ctf-misc（binwalk/foremost/volatility3）
```

## Awesome CTF 工具清单（精选）

```
编码/加密：CyberChef, CyberChef（本地版）
PWN：pwntools, ROPgadget, ropper, one_gadget, gdb-gef, pwndbg
逆向：Ghidra, IDA Free, radare2, frida, angr, Capstone
Web：sqlmap, dirb, gobuster, Burp Suite, wfuzz
取证：binwalk, foremost, volatility3, Wireshark, exiftool, steghide, zsteg
Crypto：RSACTFTool, YAFU, sage, gmpy2, CyberChef
```

## 依赖安装

```bash
pip install pycryptodome capstone pefile Pillow scapy requests
pip install gmpy2 sympy hashpumpy
pip install RSACTFTool  # git clone 后安装
# macOS: brew install radare2 ghidra binwalk
```
