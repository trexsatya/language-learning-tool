


```shell
docker buildx build --platform "linux/amd64" -t trexsatya/ghpages-backend .
docker push trexsatya/ghpages-backend  
```

Add to nginx conf file:
``` 
location / {
            proxy_set_header   X-Forwarded-For $remote_addr;
            proxy_set_header   Host $http_host;
            proxy_pass         "http://0.0.0.0:5000";
    }
```
 
