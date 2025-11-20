# Railway Build Timeout Fix

## Problem
Railway build is timing out during the "importing to docker" step. The build logs show:
- `COPY /app/.` steps taking 123m, 376m, 38m
- Build eventually times out

## Root Causes
1. **Large files being copied**: `data/logs/` directory and other unnecessary files are being included in the build
2. **Heavy dependencies**: `sentence-transformers` downloads large model files during installation
3. **No build exclusions**: Railway is copying the entire project directory

## Solutions Applied

### 1. Created `.nixpacksignore`
This file excludes unnecessary files from the Railway build:
- `data/logs/` directory (runtime data, not needed for build)
- Test files
- Documentation
- IDE files
- Python cache files
- Frontend build artifacts

### 2. Optimized `railway.json`
Added `--no-cache-dir` flag to pip install to reduce build size:
```json
"buildCommand": "cd backend && pip install --no-cache-dir -r requirements.txt"
```

## Next Steps

1. **Commit and push** these changes:
   ```bash
   git add .nixpacksignore railway.json
   git commit -m "Fix Railway build timeout: exclude data files and optimize build"
   git push
   ```

2. **Monitor the next build** - it should be faster now

3. **If still timing out**, consider:
   - Using a lighter model for `sentence-transformers` (specify model in code)
   - Splitting the build into multiple stages
   - Using Railway's build cache more effectively

## Additional Notes

- The `.nixpacksignore` file works similarly to `.dockerignore`
- Railway uses Nixpacks builder, which respects `.nixpacksignore`
- Data files will be created at runtime, not during build

