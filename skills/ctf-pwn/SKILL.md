---
name: ctf-pwn
description: CTF PWN 深度 — 栈溢出/ROP/格式化字符串/堆漏洞（tcache/unlink/UAF/House of ×7）/整数溢出。融合 ctf-wiki pwn 独家深度 + google-ctf 真实 challenge + pwntools 模板
version: 1.0
tags: [ctf, pwn, stack-overflow, rop, heap, fmtstr, uaf, house-of, tcache, glibc]
---

# CTF PWN — 漏洞利用深度融合

参考来源：
- **ctf-wiki**（`~/ctf-wiki/docs/zh/docs/pwn/`）— 独家深度，glibc 源码分析，ptmalloc2 实现
- **google-ctf**（`~/google-ctf/ctf-{year}/`）— 真实 challenge 结构
- **ctf-skills**（`~/ctf-skills/ctf-pwn/`）— 决策树 + pwntools 模板

---

## 漏洞分类决策树

```
拿到 binary，先 checksec
├── 32位 / 64位？
├── NX disabled？→ 优先考虑 shellcode
├── PIE enabled？
│   ├── PIE + Partial RELRO → .text 可预测地址
│   └── Full RELRO → 很难写 .got
└── Canary？
    ├── 有 canary → 泄露（格式化字符串/溢出 low byte）或劫持 __stack_chk_fail
    └── 无 canary → 直接栈溢出
```

---

## 栈溢出（Stack Overflow）

### Basic ROP — CTF-Wiki 核心路径

ctf-wiki 位置：`pwn/stackoverflow/x86/basic-rop.md`

```
无 PIE + 无 NX + 无 Canary：
→ 直接 ROP，跳过 /bin/sh 或 system()

有 PIE + 无 Canary：
→ Leak libc 地址 → 算 one_gadget / system 地址
```

pwntools 模板：
```python
from pwn import *
io = process('./binary')
# Leak libc
io.sendlineafter(b':', b'%15$p')  # leak libc address
io.recvline()
libc_leak = int(io.recvline().strip(), 16)
libc_base = libc_leak - 0xXXXXX  # from libc database
system = libc_base + libc_offset
binsh = libc_base + binsh_offset
io.sendline(flat({offset: p64(rdi), offset+8: p64(binsh), offset+16: p64(system), offset+24: p64(0)}))
```

### Medium ROP — Return to libc（CTF-Wiki: `pwn/stackoverflow/x86/medium-rop.md`）

```
两件事必须做：找 /bin/sh 字符串 + 找 system 函数
找 gadget：ROPgadget --binary ./binary --ropchain
```

### Fancy ROP — CTF-Wiki: `pwn/stackoverflow/x86/fancy-rop.md`

Vsyscall / SVE（Scalar Vector Extensions）利用，ret2vdso。

---

## 格式化字符串漏洞

**ctf-wiki**：`pwn/fmtstr/`（823 行深度）

```
判断漏洞：输入里有 %x, %p, %s 而没有对应参数 → 格式化字符串
判定距离：AAAA %p%p%p%p%p%p → 找 "0x41414141" 在第几个 %p

泄露 libc：
  → %15$x 泄露 got 表项
  → 计算 libc_base
  
覆写 got：
  → %{hi}$n → 4 字节写入
  → %{hi}%{lo}$hn → 2 字节写入（精确控制）
```

**高级利用（House of Corrosion 等）**：
- House of Orange（利用 top chunk）
- House of Force（溢出伪造 top chunk size，绕过 mmapsify 检查）
- House of Einherjar（溢出伪造 prev_size + PREV_INUSE，清零绕过 unlink）
- House of Lore（small bin attack 改 fd/bk）
- House of Spirit（free 伪造 chunk 触发 fd poisoning）

---

## 堆漏洞 — CTF-Wiki 独家深度

### Tcache Attack（CTF-Wiki: `pwn/heap/ptmalloc2/tcache-attack.md`）

```
Tcache（glibc 2.26+）：每线程缓存，free 时不走 unsorted bin，直接插入 tcache
特性：无 check（size 检查宽松），单链表（fd），可 double free（key 绕过）

Tcache Poisoning：改 fd 指向任意地址 → 下次 malloc 分配到目标
Tcache Stashing Unlink：small bin 回填时 poisoned + unlink 混合攻击
```

**利用步骤：**
1. 分配 ≥2 chunk，溢出/改 fd
2. 控制 tcache fd 指向 `__free_hook` 或 `__malloc_hook`
3. 分配两次：第一次拿目标 chunk，第二次分配到 hook
4. 写入 one_gadget / system 地址

### Unlink（CTF-Wiki: `pwn/heap/ptmalloc2/unlink.md`，1431 行）

```
攻击核心：unlink 宏的 fd->bk 和 bk->fd 检查被绕过（glibc < 2.26）
绕过技术：溢出修改 FD->bk = FD+0x18, BK->fd = BK+0x10
→ 修改任意地址为任意值

触发路径：
  free() → glibc malloc.s: _int_free()
  → 检查 PREV_INUSE(next_chunk) == 0 → 触发 unlink
```

### Use After Free（CTF-Wiki: `pwn/heap/use-after-free.md`）

```
常见模式：分配→使用→free→再分配（同一大小）→ 覆写
适用场景：fastbin（2.26 前的链表结构 vs 2.26+ tcache）
```

**UAF 读**：tcache Poisoning + partial overwrite（改 low byte 重建链）
**UAF 写**：覆写函数指针（free_hook / malloc_hook / _IO_FILE vtable）

### Heap Overflow（CTF-Wiki: `pwn/heap/heap-overflow.md`）

```
直接溢出 next chunk：覆写 size/PREV_INUSE/prev_size
→ 触发 consolidate（向后合并）或 overlap chunks
```

### Off By One（CTF-Wiki: `pwn/heap/off-by-one.md`）

```
溢出一个字节：0x00 ~ 0xff
利用：overlap chunk（改 low byte 使 prev_size 不等于实际大小）
→ 触发 malloc_consolidate → unlink fake chunk
```

---

## House of 系列（CTF-Wiki: `pwn/heap/house-of-series/`）

| House | 原理 | 关键前提 |
|-------|------|---------|
| House of Force | top chunk size 溢出伪造 | 无 mmap threshold 检查 |
| House of Einherjar | 溢出 prev_size + PREV_INUSE=0 | unlink size 检查绕过 |
| House of Orange | 利用 top chunk 释放→ unsorted bin | FSOP _IO_flush_all_lockp |
| House of Lore | small bin attack 改 fd/bk | 手动构造 fake chunk |
| House of Spirit | free 伪造 fastbin chunk | 需提前布置 fake chunk |
| House of Corrosion | setcontext + tcache Stashing | FSOP + environ |
| House of Reindeer | heap spraying + io_list_all | tcache dup + unsorted bin |

---

## 整数溢出（CTF-Wiki: `pwn/integeroverflow/`）

```
有符号整数溢出：int8 → 127+1 = -128 → size 变成负数 → malloc(负数) = large bin
无符号整数溢出：0xFFFFFFFF + 1 = 0 → malloc(0) 分配最小 chunk
```

---

## Google CTF PWN 题目结构

每道题：
```
~/google-ctf/ctf-{year}/quals/
  ├── challenge.yaml    # category: pwn, difficulty: easy/medium/hard
  ├── challenge/
  │   ├── Dockerfile    # 靶场环境
  │   ├── files/        # binary + libc + flags
  │   └── docker-compose.yml
  └── solves/           # 官方解法脚本
```

**解法参考**：
```bash
ls ~/google-ctf/ctf-2024/quals/ | grep -i pwn  # 列出所有 pwn 题
cat ~/google-ctf/ctf-2024/quals/{pwn-name}/solves/solution.py  # 看官方解法
```

---

## pwntools 决策树速查

```
1. 找漏洞：
   · checksec ./binary
   · ghidra 反编译 + pwntools cyclic 测偏移
   
2. 泄露：
   · FormatString: io.sendline(b'%p'*20)
   · ROP: io.sendlineafter(b':', b'%15$p')  
   
3. 利用：
   · ROP: ROPgadget + ropper + one_gadget
   · Heap: patchelf + libc-database 配对
   · fmtstr: fmtstr_payload(offset, {got_addr: value})
   
4. 稳定版本：
   · libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')
   · one_gadget libc | grep "rbp"  # 选可用 gadget
```

---

## 常用路径速查

| 内容 | 路径 |
|------|------|
| CTF-Wiki PWN 入口 | `~/ctf-wiki/docs/zh/docs/pwn/` |
| ROP 基础/中级/Fancy | `~/ctf-wiki/docs/zh/docs/pwn/stackoverflow/x86/` |
| 格式化字符串 | `~/ctf-wiki/docs/zh/docs/pwn/fmtstr/` |
| Tcache Attack | `~/ctf-wiki/docs/zh/docs/pwn/heap/ptmalloc2/tcache-attack.md` |
| Unlink | `~/ctf-wiki/docs/zh/docs/pwn/heap/ptmalloc2/unlink.md` |
| UAF | `~/ctf-wiki/docs/zh/docs/pwn/heap/use-after-free.md` |
| House of ×7 | `~/ctf-wiki/docs/zh/docs/pwn/heap/house-of-series/` |
| Integer Overflow | `~/ctf-wiki/docs/zh/docs/pwn/integeroverflow/` |
| glibc 2.35+ 改动 | `~/ctf-wiki/docs/zh/docs/pwn/heap/ptmalloc2/` (注意事项) |

---

## 注意事项

- glibc 2.35+ 已移除 `__malloc_hook`/`__free_hook`，改用 `__rtld_global` 或 `mp_.tcache_bins`
- glibc 2.34+ 的 `libc.so` 所有函数地址不再内嵌，需用 `fsop` 或 `setcontext`
- House of Orange 需要 `FSOP`（`_IO_FILE_plus` vtable hijack）配合
- Tcache double free 检测：`key` 字段（glibc 2.27+）设为此 chunk 地址，绕过需把 key 清零
