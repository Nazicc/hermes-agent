---
name: arxiv
description: "Use when searching and retrieving academic papers from arXiv using their free REST API. Search by keyword, author, category, or ID. No API key needed. Combine with web_extract or ocr-and-documents skill for full paper content. NOT for: non-arXiv papers, PDF annotation, or when Google Scholar is more appropriate."
category: research
version: 1.0.0
...
author: Hermes Agent
...
license: MIT
...
---

## Overview

This skill enables searching and retrieving academic papers from [arXiv](https://arxiv.org/) using their free REST API. It requires no API key and supports searching by keyword, author, category, or paper ID.

## API

**Endpoint**: `http://export.arxiv.org/api/query`

**Method**: GET

**Parameters**:
- `search_query`: The query string (e.g., `all:electron`, `au:smith`, `cat:cs.AI`)
- `start`: Result offset (for pagination)
- `max_results`: Maximum number of results (default: 10, max: 2000)
- `sortBy`: `relevance`, `lastUpdatedDate`, `submittedDate`
- `sortOrder`: `ascending` or `descending`

## Usage

### Search by keyword

bash
curl "http://export.arxiv.org/api/query?search_query=all:transformer&max_results=5&sortBy=submittedDate&sortOrder=descending"


### Search by author

bash
curl "http://export.arxiv.org/api/query?search_query=au:hinton&max_results=10"


### Search by category

bash
curl "http://export.arxiv.org/api/query?search_query=cat:cs.AI&max_results=20"


### Get paper by ID

bash
curl "http://export.arxiv.org/api/query?id_list=2301.00001,2301.00002"


## Reading Full Papers

For full paper content:
1. Download the PDF via the arXiv link in the feed
2. Use the `web_extract` skill to extract text from the PDF URL, or
3. Use the `ocr-and-documents` skill with `marker-pdf` for scanned documents

## Notes

- arXiv is a preprint server; papers may not be peer-reviewed
- Use for research, not for citing as final authoritative sources
- Rate limiting: be respectful, avoid bulk downloads
