---
name: reddit-community-engagement
description: "Build Reddit karma. Use when posting or promoting on Reddit."
author: Narusya
version: 1.0.0
license: MIT
category: social-media
tags: [reddit, karma, community, promotion, social-media]
metadata:
  hermes:
    tags: [reddit, karma, community, promotion, social-media]
    related_skills: [browser-tool-troubleshooting]
---

# Reddit Community Engagement

## When to use this skill

- Building karma on a new or low-karma Reddit account
- Posting comments to establish credibility before promotional posts
- Promoting projects, tools, or services on Reddit
- Troubleshooting why Reddit comments or posts aren't appearing

## Karma thresholds

- **0-50 karma**: Account is heavily rate-limited. Comments may be silently dropped. Promotional posts will be removed by filters.
- **50-100 karma**: Basic credibility. Some subreddit restrictions lift. Promotional posts may stick if the account is old enough.
- **100+ karma**: Full participation in most subreddits. Promotional posts have a reasonable chance of surviving.
- **Account age matters**: An account needs to be at least 30 days old for most subreddit participation. 45+ days is safer.

## Critical pitfall: Reddit silently drops comments from low-karma accounts

Reddit does not return an error when a comment fails to post from a low-karma account. The UI shows the comment as submitted, but it never appears on the user's profile or in the thread. There is no feedback loop.

**Always verify** by checking the user's profile page (`https://www.reddit.com/user/USERNAME/`) after posting. If the comment count doesn't increase, the comment was silently dropped.

## Critical pitfall: JS DOM manipulation does not update React state

Reddit's comment form is built with React. Setting `textarea.value` via JavaScript (e.g., `document.querySelector('textarea').value = 'text'`) updates the DOM but does NOT update React's internal state. The submit button remains disabled because React doesn't know the textarea has content.

**What appears to work but doesn't:**
- Setting `textarea.value` via JS, then dispatching `input` events — React may partially pick up the change but the comment still gets dropped server-side
- Using `Ctrl+Enter` to submit after JS injection — the form submits but Reddit's backend silently rejects it

**What actually works:**
- Manual typing through the browser UI (real keyboard input events)
- Reddit's official API (OAuth2) — requires registering an app at reddit.com/prefs/apps
- Reddit's mobile app or official clients

## Recommended karma-building strategy

1. **Don't try to automate comment posting** — manual interaction is required for low-karma accounts
2. **Target small, active subreddits** where your expertise is relevant (r/commandline, r/Python, r/selfhosted, r/homelab, r/programming)
3. **Answer questions genuinely** — helpful, specific answers with code examples or real experience
4. **Avoid promotional language** — even mentioning your own project in a comment can trigger spam filters
5. **Be patient** — karma builds slowly. 1-2 comments per day is sustainable; bursts trigger rate limits
6. **Check your karma daily** — verify comments actually posted by visiting your profile

## OAuth2 API approach (for automation)

If you need to automate Reddit interaction:
1. Register an app at https://www.reddit.com/prefs/apps (type: "script")
2. Store client_id and client_secret securely
3. Use the OAuth2 flow: `POST https://www.reddit.com/api/v1/access_token` with `grant_type=password`
4. Use the access token for API calls: `POST https://oauth.reddit.com/api/comment` with `thing_id` and `text`
5. The API returns explicit success/failure — no silent drops

**Note:** The API has its own rate limits (60 requests per minute for OAuth2). Respect them.

## Subreddit-specific rules

- Most subreddits require minimum karma (often 50-100) to post
- Some subreddits require minimum account age (30-90 days)
- r/SideProject, r/ShowOff, r/InternetIsBeautiful are common targets for project promotion but have strict anti-spam filters
- Read each subreddit's rules before posting — many have specific formatting requirements or posting schedules
- When in doubt, ask moderators before posting promotional content

## What NOT to do

- Don't use JS injection to type comments — it doesn't work with React
- Don't post multiple comments in quick succession from a new account — triggers spam filters
- Don't use the same comment text across multiple subreddits — Reddit detects cross-posting
- Don't create multiple accounts to build karma faster — this violates Reddit's TOS and risks permanent bans
- Don't delete and repost comments — Reddit tracks this and may shadowban

## Related

- `browser-tool-troubleshooting` — for browser automation issues that affect Reddit interaction
