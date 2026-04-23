---
name: oss-forensics
description: |
  Supply chain investigation, evidence recovery, and forensic analysis for GitHub repositories.
  Covers deleted commit recovery, force-push detection, IOC extraction, multi-source evidence
  collection, hypothesis formation/validation, and structured forensic reporting.
  Inspired by RAPTOR's 1800+ line OSS Forensics system.
category: security
triggers:
  - "investigate this repository"
  - "investigate [owner/repo]"
  - "check for supply chain compromise"
  - "recover deleted commits"
  - "forensic analysis of [owner/repo]"
  - "was this repo compromised"
  - "supply chain attack"
  - "suspicious commit"
  - "force push detected"
  - "IOC extraction"
toolsets:
  - terminal
  - web
  - file
  - delegation
license: MIT
metadata:
  hermes:
    tags: []
    related_skills: []
---