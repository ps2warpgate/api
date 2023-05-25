# api
## Features
- `/zones` Zone/continent states
- `/alerts` In-progress alerts
- `/population` World and zone population
- `/ws` Websocket for realtime alerts (beta)

See `/docs` for OpenAPI documentation
***

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
