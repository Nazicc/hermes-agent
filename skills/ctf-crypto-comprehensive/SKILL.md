---
name: ctf-crypto-comprehensive
description: CTF 密码学综合 — 融合 ctf-skills 脚本模板（crypto_toolkit.py/TEA/XTEA/esoteric_decoder.py）+ ctf-wiki 理论深度（RSA/Coppersmith/ECC/AEAD）+ awesome-ctf 工具链（RSACTFTool/CyberChef）
version: 1.0
tags: [ctf, crypto, rsa, aes, cipher, cryptography, coppersmith, rsactftool]
---

# CTF Crypto — 密码学综合

参考来源：
- **ctf-skills crypto**（`~/ctf-skills/ctf-crypto/`）— 脚本模板
- **ctf-wiki**（`~/ctf-wiki/docs/zh/docs/crypto/`）— 深度理论
- **awesome-ctf**（`~/awesome-ctf/README.md`）— 工具链

## 决策树

```
看见加密/编码/哈希题
├── 编码（base64/hex/ascii）→ crypto_toolkit.py encode/decode
├── 古典密码（凯撒/栅栏/摩斯/培根）→ esoteric_decoder.py
├── 流密码（XOR/RC4）→ crypto_toolkit.py xor_decipher
│   └── 维吉尼亚 → ctf-wiki crypto/classical/vigenere/
├── 分组密码（AES/DES/3DES）→ AES CBC/CTR/ECB 模式判断 + 密钥暴力
├── RSA → ctf-wiki crypto/asymmetric/rsa/ + RSACTFTool
│   ├── e=3 且 m^3 < N → 直接开立方根
│   ├── 共模攻击 → 相同 N，不同 e
│   ├── e 很小（小公钥指数）→ m = c^e mod N 开方
│   ├── p/q 接近 → boneh_durfee（e ≈ N^0.292）
│   ├── Coppersmith →已知 m 高位，攻击 d 或 p
│   └── Wiener → e/d 比值小，Wiener 攻击
├── ECC → ctf-wiki crypto/asymmetric/ECC/
│   ├── 离散对数 → sage: discrete_log()
│   └── 曲线参数弱 → 直接用公开参数解
├── AEAD（GCM/CTR）→ ctf-wiki crypto/aead/
│   └── 认证位翻转 → IV 改变不影响密文完整性
└── 哈希长度扩展 → hashpumpy（MD5/SHA-256）
```

---

## RSA 深入攻击链（CTF-Wiki: `crypto/asymmetric/rsa/` 641 行）

### 核心判别

```
1. N = p × q → 分解 N
   - factordb.com 查
   - rsactftool.py 分解
   - yafu 本地分解

2. e 与 φ(N) 不互素 → 非标准 RSA

3. e 很小 → 直接开方
   >>> m = int(pow(c, 1/e, N))  # 或用 sage
```

### 工具链

```bash
# RSACTFTool — 所有标准 RSA 攻击
python3 ~/ctf-skills/ctf-crypto/RSACTFTool.py --private --inputkeys n e c

# Coppersmith（HNP - Hidden Number Problem）
sage solve.sage

# Wiener 攻击
python3 ~/ctf-skills/ctf-crypto/wiener.py n e

# Hash Length Extension
python3 -c "import hashpumpy; print(hashpumpy.hashpump(...))"
```

### Coppersmith 判别条件

```
条件：m 高位已知（d 低位泄露）或 p/q 高位已知
sage:
  n = ...
  e = ...
  PR.<x> = PolynomialRing(Zmod(n))
  m = int(pow(c, d, n))  # d 从泄露得到
  # 求 m_mod = m & ((1 << 330)-1)  # 已知高位
  # Coppersmith：已知 (m_mod) 求 m 全值
```

### CTF-Wiki RSA 深度攻击列表

```
crypto/asymmetric/rsa/
├── low_exponent/      # e=3 直接开立方
├── common_factor/     # N1, N2 有公因子 → gcd 分解
├── cube_root/         # m^3 < N → 直接开方
├── fermat/            # p,q 接近 → 费马分解
├── coppersmith/       # HNP, Franklin-Reiter, 更多位泄露
├── broadcast/         # 中国剩余定理（Håstad 广播攻击）
├── bleichenbacher/   # Oracle 侧信道攻击
└── pkcs1/            # Pkcs1 v1.5 填充攻击
```

---

## 古典密码脚本

### esoteric_decoder.py（ctf-skills）

```bash
# 摩斯电码
python3 ~/ctf-skills/ctf-crypto/esoteric_decoder.py -i morse -e ".... . .-.. .-.. ---"

# 二进制
python3 ~/ctf-skills/ctf-crypto/esoteric_decoder.py -i binary -e "01000110 01001100"

# 栅栏密码
python3 ~/ctf-skills/ctf-crypto/esoteric_decoder.py -i railfence -e "密文" -k 3
```

### crypto_toolkit.py（ctf-skills）

```python
from ~/ctf-skills/ctf-crypto.crypto_toolkit import *

# TEA / XTEA 解密
key = b'1234567890abcdef'
cipher = bytes.fromhex('...')
plain = tea_decrypt(cipher, key)

# XOR
plain = xor_decipher(ciphertext, keystream)

# 编码
encoded = base64_encode(plain)
hex_encoded = hex_encode(plain)
```

---

## Hash Length Extension Attack

```python
import hashpumpy

original_msg = b"admin=false"
original_sig = "..."

# 在原消息后追加数据
new_msg, new_sig = hashpumpy.hashpump(
    original_sig,  # 原始 MAC/SIG
    original_msg,  # 原始消息
    b"&admin=true",  # 追加数据
    16  # 哈希块长度（MD5=16, SHA1=20, SHA256=32）
)
print(new_msg)  # 发送这个
print(new_sig)  # 发送这个签名
```

---

## AES 攻击模式

| 模式 | 攻击向量 | 工具 |
|------|---------|------|
| ECB | 相同块→相同密文→明文块模式分析 | CyberChef |
| CBC | Bit-flip IV → 任意块翻转 | xor_decipher + 手动修复 padding |
| CTR |Nonce 重用 → 密文 XOR | xor_decipher |
| GCM | 认证位翻转 | 改 IV，低位影响 tag |

---

## 常用路径速查

| 内容 | 路径 |
|------|------|
| RSA 攻击全家桶 | `~/ctf-wiki/docs/zh/docs/crypto/asymmetric/rsa/` |
| ECC 攻击 | `~/ctf-wiki/docs/zh/docs/crypto/asymmetric/ECC/` |
| 分组密码 AES/DES | `~/ctf-wiki/docs/zh/docs/crypto/symmetric/` |
| AEAD 认证加密 | `~/ctf-wiki/docs/zh/docs/crypto/aead/` |
| 流密码 RC4 | `~/ctf-wiki/docs/zh/docs/crypto/streamcipher/` |
| LCG 伪随机数 | `~/ctf-wiki/docs/zh/docs/crypto/prng/` |
| 哈希长度扩展 | `~/ctf-wiki/docs/zh/docs/crypto/hash/` |
| 古典密码 | `~/ctf-wiki/docs/zh/docs/crypto/classical/` |

## 工具安装

```bash
pip install gmpy2 sympy pycryptodome
sage  # brew install sage 或 conda install sage
python3 -m pip install RSACTFTool
```

---

## CTF-Wiki Crypto 独家深度

- **RSA PKCS#1 v1.5**：`Bleichenbacher` Oracle 攻击（ROCA）、Manger 攻击
- **Coppersmith 定理**：`sage` 实现，求 HNP 全套解法
- **ECC 离散对数**：`smart-attack`（p 是小素数）、` MOV-attack`（超奇异曲线）
- **AEAD-GCM**：认证标签截断、IV 重用导致密文 XOR 可预测
- **侧信道**：功率分析、Cache timing（CTF 中少见但 CTF-Wiki 有覆盖）
