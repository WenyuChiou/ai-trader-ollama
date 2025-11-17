# Troubleshooting Guide

## Common Issues

### API Server Not Starting

**Symptoms**:
- Port 8000 already in use
- Ollama connection failed
- Python module not found

**Solutions**:
1. Check port availability:
   ```powershell
   .\scripts\check_port.ps1
   ```

2. Stop existing processes:
   ```powershell
   .\scripts\stop_all_services.ps1
   ```

3. Check Ollama:
   ```powershell
   ollama list
   ```

4. Check Python environment:
   ```powershell
   python --version
   cd backend
   .\venv\Scripts\Activate.ps1
   ```

### No Orders Generated

**Symptoms**:
- Trading cycle runs but no orders
- Market is open but agent doesn't trade

**Diagnosis**:
```powershell
python scripts\diagnose_no_trades.py
```

**Common Causes**:
1. Market is closed
2. Agent decided not to trade
3. Daily order limit reached
4. No recommended stocks
5. Insufficient cash

**Solutions**:
- Check market status: `GET /api/market/is-open`
- Check agent conversations: `GET /api/agents/conversations`
- Check portfolio state: `GET /api/portfolio/real-time`
- Review agent decisions in logs

### P&L Calculation Issues

**Symptoms**:
- Unrealized P&L shows 0
- Market value equals cost basis
- Prices not updating

**Solutions**:
1. Check market is open (real-time prices only during market hours)
2. Verify API is fetching prices correctly
3. Check `positions_detail` in API response
4. Refresh frontend to reload data

### Memory/Conversation Logs Missing

**Symptoms**:
- No conversation entries
- Missing agent logs
- Memory files not created

**Solutions**:
1. Check `data/logs/discussion_actions.jsonl` exists
2. Verify write permissions
3. Check disk space
4. Review error logs for write failures

### Frontend Not Updating

**Symptoms**:
- Dashboard shows old data
- Charts not updating
- Market status stuck

**Solutions**:
1. Hard refresh browser (Ctrl+F5)
2. Check API is running
3. Check browser console for errors
4. Verify API endpoints are accessible
5. Clear browser cache

## Error Codes

### API Errors

**500 Internal Server Error**
- Check server logs
- Verify configuration files
- Check data file permissions

**404 Not Found**
- Verify endpoint URL
- Check API routes
- Verify file paths

**400 Bad Request**
- Check request format
- Verify parameters
- Check data types

## Debug Mode

Enable debug logging:
```python
# In config.json
{
  "debug": true,
  "log_level": "DEBUG"
}
```

## Getting Help

1. Check logs: `data/logs/`
2. Run diagnostics: `python scripts/verify_system_status.py`
3. Check system features: `python scripts/check_system_features.py`
4. Review documentation

## See Also
- [Quick Start Guide](QUICK_START.md)
- [Configuration Guide](CONFIGURATION.md)
- [API Reference](API_REFERENCE.md)
