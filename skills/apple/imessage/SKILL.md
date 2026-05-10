---
name: imessage
description: Send and receive iMessages/SMS via the imsg CLI on macOS.
category: general
---

Send and receive iMessages and SMS messages using the `imsg` CLI tool on macOS.

**Prerequisites:**
- macOS with the `imsg` command-line tool installed
- Apple ID configured for iMessage

**Usage:**

bash
# Send a message
imsg send "+1234567890" "Hello, this is a test message"
imsg send "contact@email.com" "Message via iMessage"

# Read recent messages
imsg list
imsg read "+1234567890"

# Reply to a conversation
imsg reply "+1234567890" "Thanks for the message!"

# Check unread messages
imsg unread


**Best Practices:**
- Always verify recipient contact before sending
- Use full international format for phone numbers (+1XXXXXXXXXX)
- For group messages, specify multiple recipients
- Check `imsg --help` for additional commands and options

**Notes:**
- Requires macOS and Apple’s iMessage service
- SMS requires cellular plan or connected iPhone
- Messages sync across Apple devices signed into the same Apple ID

**Upgrade Path:**
This is a stub — no RIA-TV++ sections yet. Upgrade path: add A2 (trigger scenarios), R (imsg CLI reference), I (methodology), A1/A2 (examples), E (error codes), B (boundary conditions).
