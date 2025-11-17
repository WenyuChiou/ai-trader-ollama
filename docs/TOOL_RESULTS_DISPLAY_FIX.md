# Tool Results Display Fix & Discussion Rounds Panel

## Issue Summary

### Problem 1: Tool Results Not Displaying
- **Error**: Tool results were not showing when filtering by agent (e.g., MarketAnalyst, SentimentAnalyst)
- **Root Cause**: Tool entries in `discussion_actions.jsonl` had `agent` field set to `"ToolSystem"` instead of the actual agent name that called the tool
- **Impact**: Frontend could not match tool results to their respective agents when filtering

### Problem 2: Discussion Coordinator Display Format
- **Error**: Discussion Coordinator content showed merged format like "Market Analyst: ... | Technical Analyst: ... | Fundamental Analyst: ..."
- **User Request**: Display each agent's analysis separately in a dedicated panel, with clear separation between rounds

## Solutions Implemented

### 1. Tool Results Display Fix

**File**: `backend/src/orchestrator/trading_cycle.py`

**Change** (Line 713):
```python
# Before:
"agent": "ToolSystem",  # Tool entries had generic agent name

# After:
"agent": agent_name,  # Use actual agent name (MarketAnalyst, TechnicalAnalyst, etc.)
```

**Impact**:
- Tool entries now correctly identify which agent called each tool
- Frontend can properly filter and display tool results by agent
- Each agent's tool usage is now traceable

### 2. Discussion Rounds Panel

**File**: `frontend/monitor.html`

**Implementation** (Lines 3718-3811):
- Created dedicated Discussion Rounds Panel that displays before conversation list
- Uses `discussion_rounds_summaries` data from API
- Displays each round (Round 1, Round 2, Round 3) separately
- Within each round, displays agents in fixed order:
  - MarketAnalyst
  - TechnicalAnalyst
  - FundamentalAnalyst
  - SentimentAnalyst
  - DiscussionCoordinator

**Display Features**:
- Each round has its own card with clear header
- Each agent has its own sub-card with:
  - Agent icon and name
  - Stance badge (with color coding)
  - Tools used list
  - Full summary text
- Color-coded left border based on stance (bullish/bearish/neutral)

**Benefits**:
- Clear separation between discussion rounds
- Easy to see each agent's independent analysis
- Better organization than merged Discussion Coordinator content
- Stance and tools are clearly visible for each agent

## Technical Details

### Data Flow

1. **Backend** (`trading_cycle.py`):
   - Tool calls are logged with correct `agent` field
   - Discussion rounds are stored in `discussion_rounds_summaries` structure

2. **API** (`server.py`):
   - `/api/agents/conversations` endpoint returns `discussion_rounds_summaries`
   - Structure: `{ "1": [{agent, summary, stance, tools_used}, ...], "2": [...], "3": [...] }`

3. **Frontend** (`monitor.html`):
   - `renderConversations()` function receives `discussionRoundsSummaries`
   - Creates Discussion Rounds Panel before conversation list
   - Each round displays all agents' analyses separately

### Discussion Coordinator Content Formatting

**File**: `frontend/monitor.html` (Lines 4103-4147)

**Enhancement**:
- Discussion Coordinator content is still formatted for display in conversation list
- However, the dedicated Discussion Rounds Panel provides better visibility
- Coordinator's merged content is now less critical since each agent's analysis is shown separately

## Testing

### Verification Steps

1. **Tool Results Display**:
   - Open frontend and click on agent filter buttons (Market, Technical, Fundamental, Sentiment)
   - Verify that tool results appear for each agent
   - Check that tool names and results are correctly displayed

2. **Discussion Rounds Panel**:
   - Open conversations modal
   - Verify Discussion Rounds Panel appears at the top
   - Check that each round (1, 2, 3) is displayed separately
   - Verify each agent's analysis is shown with stance, tools, and summary

3. **Data Consistency**:
   - Verify tool entries in `discussion_actions.jsonl` have correct `agent` field
   - Check that `discussion_rounds_summaries` contains all rounds and agents

## Related Files

- `backend/src/orchestrator/trading_cycle.py` - Tool logging with correct agent names
- `frontend/monitor.html` - Discussion Rounds Panel implementation
- `backend/src/api/server.py` - API endpoint returning `discussion_rounds_summaries`

## Date

Fixed: 2025-01-XX

