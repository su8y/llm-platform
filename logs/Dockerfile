FROM docker:27-cli

WORKDIR /app

# bash 설치
RUN apk add --no-cache bash

COPY collect_logs.sh .
RUN chmod +x collect_logs.sh

CMD ["bash", "./collect_logs.sh"]