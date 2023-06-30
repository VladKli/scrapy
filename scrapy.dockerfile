FROM vimagick/scrapyd

WORKDIR /scrapy

#RUN apt-get update && apt-get upgrade -y

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD set -m; scrapyd & cd chemicals && scrapyd-deploy default & cd .. && fg scrapyd

