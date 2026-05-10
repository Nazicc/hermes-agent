---
name: baoyu-infographic
description: "Generate professional infographics with 21 layout types and 21 visual styles. Analyzes content, recommends layout×style combinations, and generates publication-ready infographics. Use when user asks to create \"infographic\", \"visual summary\", \"信息图\", \"可视化\", or \"高密度信息大图\". Also use when you need to create visual diagrams, charts, concept maps, or graphic infographics, or convert text-based content into visual representations."
category: general
---

# Infographic & Visual Generation

## Overview

This skill handles the creation of visual diagrams, charts, concept maps, and graphic infographics. Analyzes content, recommends layout×style combinations, and generates publication-ready infographics with 21 layout types and 21 visual styles.

## Use When

- You need to create a visual diagram from text or data
- You need to convert structured information into a graphic representation
- You need concept maps, flowcharts, or visual summaries
- Asked to create "infographic", "visual summary", "信息图", "可视化", or "高密度信息大图"

## NOT for

- General-purpose shell scripting or file manipulation
- Agent health monitoring, cron job execution, or system maintenance
- Code generation, debugging, or repository exploration

## Supported Tools

- **Excalidraw**: Best for hand-drawn style diagrams and collaborative editing
- **Concept Diagrams**: Structured diagram generation from text descriptions
- **ASCII Art**: Text-based visual output for terminal environments
- **Meme Generation**: Humorous visual content from templates

## Common Workflow

1. Identify the information to visualize
2. Select the appropriate visual tool based on style and use case
3. Provide structured input (text, data, or description)
4. Generate and optionally save the output

## Diagnostic

### read_file returns empty content
If a `read_file` call returns empty content for a file you expect to exist:
1. Verify the file path is correct (check for typos, ~ expansion issues)
2. Use the terminal as a fallback: run `cat <path>` or `ls -la <parent-dir>`
3. If the file does not exist, the terminal output will confirm this explicitly
4. Do NOT keep re-calling read_file with the same path — switch to the terminal immediately

### Tool returns unexpected empty result
- Check that the input format matches the tool's expected schema
- Verify the tool is available in the current environment
- Try an alternative tool from the supported list above
