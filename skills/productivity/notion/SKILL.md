---
name: notion
description: "Use when creating and managing Notion pages, databases, and blocks via the API. Search, create, update, and query Notion workspaces directly from terminal. NOT for: non-Notion workspaces, complex database queries, or when Notion app UI is more efficient."
category: general
---

## R — Knowledge Source

- **API Base URL**: `https://api.notion.com/v1`
- **Auth**: Bearer token via `Authorization: Bearer $NOTION_API_KEY`
- **Versioning**: All requests must include `Notion-Version: 2022-06-28` (or current)
- **Rate Limits**: 3 requests/second for most integrations; 30 requests/second for enterprise
- **Pagination**: Cursor-based via `start_cursor` / `has_more` fields

## I — Core API Patterns

All operations use `curl` with JSON payloads. No SDK required.

**Headers (always required)**:
bash
-H "Authorization: Bearer $NOTION_API_KEY" \
-H "Content-Type: application/json" \
-H "Notion-Version: 2022-06-28"


**Error response format**:

{"object": "error", "status": 400, "code": "validation_error", "message": "..."}


### Key Endpoints

| Operation | Endpoint | Method |
|-----------|----------|--------|
| Search | `/search` | POST |
| Create Page | `/pages` | POST |
| Get Page | `/pages/{id}` | GET |
| Update Page | `/pages/{id}` | PATCH |
| Archive Page | `/pages/{id}` | PATCH |
| Create Block | `/blocks/{id}/children` | PATCH |
| Query Database | `/databases/{id}/query` | POST |
| Get Block | `/blocks/{id}` | GET |
| Update Block | `/blocks/{id}` | PATCH |

## A1 — Common Operations

### Search workspace
bash
curl -s -X POST "https://api.notion.com/v1/search" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Notion-Version: 2022-06-28" \
  -d '{"query": "search term", "filter": {"property": "object", "value": "page"}}'


### Create a page
bash
curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Notion-Version: 2022-06-28" \
  -d '{
    "parent": {"database_id": "<DATABASE_ID>"},
    "properties": {"<prop_name>": {"<prop_type>": "<value>"}},
    "children": [{"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Hello"}}]}}]
  }'


### Query a database
bash
curl -s -X POST "https://api.notion.com/v1/databases/<DATABASE_ID>/query" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Notion-Version: 2022-06-28" \
  -d '{"filter": {"property": "Status", "select": {"equals": "Done"}}}'


### Get a page
bash
curl -s "https://api.notion.com/v1/pages/<PAGE_ID>" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2022-06-28"


### Update page properties
bash
curl -s -X PATCH "https://api.notion.com/v1/pages/<PAGE_ID>" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Notion-Version: 2022-06-28" \
  -d '{"properties": {"<prop>": {"<type>": "<value>"}}}'


### Append blocks to a page
bash
curl -s -X PATCH "https://api.notion.com/v1/blocks/<BLOCK_ID>/children" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Notion-Version: 2022-06-28" \
  -d '{"children": [{"object": "block", "type": "heading_1", "heading_1": {"rich_text": [{"type": "text", "text": {"content": "Title"}}]}}]}'


## A2 — Trigger Scenarios

- User says "create a Notion page for [topic]" → use `POST /pages`
- User says "query my tasks database" → use `POST /databases/{id}/query`
- User says "search for pages containing [term]" → use `POST /search`
- User says "add a todo item to my Notion list" → use `POST /pages` or `PATCH /blocks/{id}/children`
- User says "update the status of [item]" → use `PATCH /pages/{id}`

## E — Edge Cases

- **Missing API key**: Response `{"object": "error", "code": "unauthorized"}` → ensure `NOTION_API_KEY` is set before calling
- **Invalid database_id**: Response `{"object": "error", "code": "validation_error"}` → verify parent ID format (32 hex chars with hyphens)
- **Rate limited**: Response `429 Too Many Requests` → back off and retry with `Retry-After` header or exponential backoff
- **Internal errors (500)**: Notion internal errors are common → retry with exponential backoff
- **Archived page**: Cannot update archived pages → unarchive first with `PATCH /pages/{id}` + `"archived": false`
- **Rich text**: All text must be wrapped in `{"type": "text", "text": {"content": "..."}}` structure
- **Database schema**: Query filter properties must match the database's actual property types (select, text, date, etc.) and property names are case-sensitive
- **Title property**: Use `"title"` array, not `"name"`

## B — Behavioral Notes

- Always include `Notion-Version` header — omitting it returns 404
- Block children are appended, not replaced (use `PATCH /blocks/{id}/children?append=true`)
- Parent for a new page can be a `database_id` (template in DB) or `page_id` (child page)
- Emoji icons: use `"icon": {"type": "emoji", "emoji": "🎯"}` in page creation
- Archived pages/databases still exist but are filtered out by default
