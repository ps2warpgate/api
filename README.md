# api
Basic API for the data collected by [ps2warpgate/aggregator](https://github.com/ps2warpgate/aggregator)  
## Run
Quick start: `uvicorn main:app --reload`  
### Docker:
```docker
docker run -d --name warpgate-api \
    -e MONGODB_URL= \
    -e MONGODB_DB= \
    -e RABBITMQ_URL= \
    -e LOG_LEVEL=INFO \
    -p 8080:80 \
    ghcr.io/ps2warpgate/api
```
