# scrapy
1. git clone git@github.com:VladKli/scrapy.git
2. pip install -r requirements.txt
3. create postgres DB, set up environmental variables. change django settings.py and scrapy settings DB connection accordingly
4. cd scrapy_api/ 
5. python manage.py makemigrations, migrate
6. cd ../chemicals
7. scrapyd
8. open the second terminal and deploy scrapy project -> scrapyd-deploy default
9. run django server from scrapy_api folder -> python manage.py runserver

<h3>Available endpoints:</h3>

chemicals/?numcas=71884-56-5 - to get info about chemicals with specific cas number

chemicals/avg/?numcas=71884-56-5 - to get an average price for 1g/ml of a chemical

chemicals/run/?company_name=AstaTech - to run a spider providing campaign name

<h3>run tests:</h3>
python manage.py test
