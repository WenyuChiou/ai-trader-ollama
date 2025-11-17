# 🔬 Comprehensive System Test Plan

## 🎯 Objective
Ensure the entire system can operate normally and continuously for several months.

---

## 📋 Test Categories

### 1. Agent Architecture Tests

#### 1.1 Tool Usage Tests
- [ ] **Tool Availability**: Verify all 23 tools are accessible and functional
- [ ] **Tool Integration**: Test tool calls from each agent
- [ ] **Tool Error Handling**: Test behavior when tools fail
- [ ] **Tool Rate Limiting**: Verify API rate limits are respected
- [ ] **Tool Response Parsing**: Ensure tool responses are correctly parsed

**Test Script**: `scripts/verify_market_and_tools.py`

#### 1.2 Agent Communication Tests
- [ ] **Multi-Agent Discussion**: Verify all 4 analysts participate in discussion
- [ ] **Discussion Coordinator**: Test coordinator synthesis of analyst views
- [ ] **Conversation Flow**: Ensure smooth conversation transitions
- [ ] **Memory Integration**: Verify agents access historical memory
- [ ] **Context Preservation**: Test that context is maintained across rounds

**Test Script**: `scripts/check_system_features.py`

#### 1.3 Order Generation Tests
- [ ] **Buy Order Generation**: Test buy order creation logic
- [ ] **Sell Order Generation**: Test sell order creation logic
- [ ] **Order Validation**: Verify orders meet position limits
- [ ] **Order Price Calculation**: Test order price accuracy
- [ ] **Order Execution**: Test order filling mechanism
- [ ] **Order Cancellation**: Test order cancellation logic

**Test Script**: `scripts/diagnose_no_trades.py`

#### 1.4 Initialization Tests
- [ ] **System Initialization**: Test `/api/system/init` endpoint
- [ ] **Portfolio Initialization**: Verify portfolio state initialization
- [ ] **Data Directory Setup**: Test data directory creation
- [ ] **Configuration Loading**: Verify config.json and agents.yaml loading
- [ ] **Memory Initialization**: Test memory system startup

**Test Script**: `scripts/check_system_pipeline.py`

---

### 2. Position & Portfolio Tests

#### 2.1 Position Recording Tests
- [ ] **Position Creation**: Verify positions are created on buy
- [ ] **Position Updates**: Test position updates on additional buys
- [ ] **Position Deletion**: Test position removal on full sell
- [ ] **Position Persistence**: Verify positions survive API restarts
- [ ] **Position Accuracy**: Verify quantity, avg_cost, total_cost accuracy

**Test Files**: `data/logs/portfolio_state.json`

#### 2.2 Equity Tracking Tests
- [ ] **Equity Recording**: Verify equity snapshots are recorded hourly
- [ ] **Equity History**: Test equity_history.jsonl updates
- [ ] **Equity Calculation**: Verify equity = cash + positions_value
- [ ] **Equity Chart Data**: Test equity chart data availability
- [ ] **Equity Persistence**: Verify equity records survive restarts

**Test Files**: `data/logs/equity_history.jsonl`

#### 2.3 P&L Calculation Tests
- [ ] **Unrealized P&L**: Test unrealized P&L calculation accuracy
- [ ] **Realized P&L**: Test realized P&L on sell orders
- [ ] **P&L Percentage**: Verify P&L percentage calculations
- [ ] **P&L Display**: Test frontend P&L display accuracy
- [ ] **P&L Real-time Updates**: Verify P&L updates with price changes

**Test Endpoint**: `/api/portfolio/real-time`

#### 2.4 Portfolio Visualization Tests
- [ ] **Equity Chart**: Test equity chart rendering
- [ ] **Position Distribution**: Test pie chart of positions
- [ ] **P&L Display**: Verify P&L color coding (green/red)
- [ ] **Real-time Updates**: Test chart updates on refresh
- [ ] **Historical Data**: Verify historical chart data loading

**Test Page**: `frontend/monitor.html`

---

### 3. Conversation & Memory Tests

#### 3.1 Conversation Logging Tests
- [ ] **Discussion Actions**: Verify all discussion rounds are logged
- [ ] **Analyst Reports**: Test individual analyst report logging
- [ ] **Coordinator Summary**: Test coordinator summary logging
- [ ] **Trader Agent Logs**: Verify trader agent decision logging
- [ ] **Risk Analyst Logs**: Test risk analyst report logging

**Test Files**: `data/logs/discussion_actions.jsonl`

#### 3.2 Memory System Tests
- [ ] **Daily Memory Creation**: Verify daily memory files are created
- [ ] **Memory Loading**: Test memory loading for context
- [ ] **Memory Cleanup**: Test old memory cleanup
- [ ] **Memory Structure**: Verify memory file structure
- [ ] **Memory Persistence**: Test memory survives restarts

**Test Files**: `data/logs/memory/daily/YYYY-MM-DD.json`

#### 3.3 Prompt Tests
- [ ] **Prompt Loading**: Verify prompts load correctly
- [ ] **Prompt Variables**: Test prompt variable substitution
- [ ] **Prompt Updates**: Test prompt update mechanism
- [ ] **Prompt Effectiveness**: Monitor agent responses to prompts
- [ ] **Prompt Versioning**: Test prompt version control

**Test Files**: `prompts/*.yml`

---

### 4. Backend API Tests

#### 4.1 API Endpoint Tests
- [ ] **Health Check**: Test `/api/health` endpoint
- [ ] **System Info**: Test `/api/system/info` endpoint
- [ ] **Market Status**: Test `/api/market/is-open` endpoint
- [ ] **Portfolio Real-time**: Test `/api/portfolio/real-time` endpoint
- [ ] **Equity History**: Test `/api/portfolio/equity-history` endpoint
- [ ] **Conversations**: Test `/api/agents/conversations` endpoint
- [ ] **Recent Trades**: Test `/api/trades/recent` endpoint
- [ ] **Execute Trade**: Test `/api/trading/execute-trade` endpoint
- [ ] **Check Pending Orders**: Test `/api/trading/check-pending-orders` endpoint

**Test Script**: `scripts/check_api_endpoints.py`

#### 4.2 API Error Handling Tests
- [ ] **404 Errors**: Test handling of missing resources
- [ ] **500 Errors**: Test handling of server errors
- [ ] **Timeout Handling**: Test API timeout behavior
- [ ] **Rate Limiting**: Test API rate limiting
- [ ] **CORS Headers**: Verify CORS headers are set correctly

#### 4.3 API Performance Tests
- [ ] **Response Time**: Test API response times
- [ ] **Concurrent Requests**: Test handling of concurrent requests
- [ ] **Load Testing**: Test system under load
- [ ] **Memory Usage**: Monitor API memory usage
- [ ] **CPU Usage**: Monitor API CPU usage

---

### 5. Frontend Tests

#### 5.1 UI Component Tests
- [ ] **Market Status Display**: Test market status indicator
- [ ] **Portfolio Summary**: Test portfolio summary display
- [ ] **Positions Table**: Test positions table rendering
- [ ] **Equity Chart**: Test equity chart rendering
- [ ] **Conversation Display**: Test conversation log display
- [ ] **Trade History**: Test trade history display

#### 5.2 Frontend-Backend Integration Tests
- [ ] **Data Fetching**: Test data fetching from API
- [ ] **Data Updates**: Test real-time data updates
- [ ] **Error Handling**: Test frontend error handling
- [ ] **Loading States**: Test loading state displays
- [ ] **Auto-refresh**: Test auto-refresh mechanism

**Test Script**: `scripts/test_frontend_features.py`

---

### 6. Railway Deployment Tests

#### 6.1 Railway Upload Tests
- [ ] **Data Upload**: Test data upload to Railway
- [ ] **Upload Script**: Test `upload_data_to_railway.py`
- [ ] **Upload Scheduling**: Test daily upload scheduling
- [ ] **Upload Error Handling**: Test upload error recovery
- [ ] **Upload Verification**: Verify uploaded data integrity

**Test Script**: `scripts/test_railway_data.py`

#### 6.2 Railway Data Sync Tests
- [ ] **Data Synchronization**: Test data sync between local and Railway
- [ ] **Conflict Resolution**: Test conflict resolution
- [ ] **Data Consistency**: Verify data consistency
- [ ] **Sync Scheduling**: Test sync scheduling

---

### 7. Long-term Stability Tests

#### 7.1 Continuous Operation Tests
- [ ] **24-Hour Run**: Test system running for 24 hours
- [ ] **7-Day Run**: Test system running for 7 days
- [ ] **Memory Leaks**: Monitor for memory leaks
- [ ] **Resource Usage**: Monitor resource usage over time
- [ ] **Error Rate**: Monitor error rate over time

#### 7.2 Data Integrity Tests
- [ ] **Data Backup**: Test data backup mechanism
- [ ] **Data Recovery**: Test data recovery from backup
- [ ] **Data Consistency**: Verify data consistency over time
- [ ] **Data Corruption**: Test handling of corrupted data

#### 7.3 Failure Recovery Tests
- [ ] **API Restart**: Test system recovery after API restart
- [ ] **Database Recovery**: Test recovery from database errors
- [ ] **Network Failure**: Test handling of network failures
- [ ] **Service Failure**: Test recovery from service failures

---

## 🧪 Test Execution Plan

### Phase 1: Pre-Test Preparation (Day 1)
1. ✅ Backup all current data
2. ✅ Clean up scripts directory
3. ✅ Update README
4. ✅ Create test environment

### Phase 2: Unit Tests (Day 2-3)
1. Run all agent architecture tests
2. Run all position & portfolio tests
3. Run all conversation & memory tests
4. Run all backend API tests

### Phase 3: Integration Tests (Day 4-5)
1. Test frontend-backend integration
2. Test Railway deployment
3. Test end-to-end trading cycle

### Phase 4: Long-term Tests (Day 6-30)
1. Run 24-hour continuous test
2. Run 7-day continuous test
3. Monitor system stability
4. Collect performance metrics

### Phase 5: Optimization (Day 31+)
1. Analyze test results
2. Implement optimizations
3. Re-test optimized system
4. Deploy to production

---

## 📊 Test Metrics

### Performance Metrics
- API Response Time: < 500ms (p95)
- Trading Cycle Time: < 60s
- Memory Usage: < 2GB
- CPU Usage: < 50% average

### Reliability Metrics
- Uptime: > 99.5%
- Error Rate: < 0.1%
- Data Loss: 0%
- Order Execution Rate: > 95%

### Accuracy Metrics
- P&L Calculation Accuracy: 100%
- Position Tracking Accuracy: 100%
- Equity Calculation Accuracy: 100%
- Market Data Accuracy: > 99%

---

## 🔍 Test Tools

### Automated Test Scripts
- `scripts/verify_system_status.py` - Overall system health
- `scripts/check_system_features.py` - Feature verification
- `scripts/check_system_pipeline.py` - Pipeline integrity
- `scripts/check_api_endpoints.py` - API endpoint tests
- `scripts/verify_market_and_tools.py` - Tool verification
- `scripts/diagnose_no_trades.py` - Trading diagnosis

### Manual Test Checklist
- [ ] Manual trading cycle execution
- [ ] Manual order verification
- [ ] Manual data inspection
- [ ] Manual UI verification

---

## 📝 Test Report Template

```markdown
# Test Report - [Date]

## Test Summary
- Total Tests: X
- Passed: Y
- Failed: Z
- Skipped: W

## Test Results by Category
### Agent Architecture
- [ ] All tests passed
- [ ] Issues found: [list]

### Position & Portfolio
- [ ] All tests passed
- [ ] Issues found: [list]

### Conversation & Memory
- [ ] All tests passed
- [ ] Issues found: [list]

### Backend API
- [ ] All tests passed
- [ ] Issues found: [list]

### Frontend
- [ ] All tests passed
- [ ] Issues found: [list]

### Railway Deployment
- [ ] All tests passed
- [ ] Issues found: [list]

## Performance Metrics
- API Response Time: X ms
- Memory Usage: X GB
- CPU Usage: X %

## Issues & Recommendations
1. [Issue description]
2. [Recommendation]

## Next Steps
1. [Action item]
2. [Action item]
```

---

## ✅ Success Criteria

System is considered ready for long-term operation when:
- ✅ All critical tests pass
- ✅ Performance metrics meet targets
- ✅ Reliability metrics meet targets
- ✅ No critical bugs found
- ✅ Documentation is complete
- ✅ Backup and recovery tested
- ✅ Monitoring and alerting configured

