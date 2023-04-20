# api
Basic API for the data collected by [ps2warpgate/aggregator](https://github.com/ps2warpgate/aggregator)  
## Run
Quick start: `uvicorn main:app --reload`  
### Docker:
```docker
docker run -d --name warpgate-api \
    -e REDIS_HOST= \
    -e REDIS_PORT= \
    -e REDIS_DB= \
    -e REDIS_PASS= \
    -e LOG_LEVEL=INFO \
    -p 8080:80 \
    ghcr.io/ps2warpgate/api
```
