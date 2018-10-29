import aylien_news_api
from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.parse import urlparse
import requests
from aylien_news_api.rest import ApiException
import sys
from flask import Markup

import html

# Configure API key authorization: app_id
aylien_news_api.configuration.api_key['X-AYLIEN-NewsAPI-Application-ID'] = '2f5e48ee'
#2: aylien_news_api.configuration.api_key['X-AYLIEN-NewsAPI-Application-ID'] = 'c0497298'
#1: aylien_news_api.configuration.api_key['X-AYLIEN-NewsAPI-Application-ID'] = '0a282753'
# Configure API key authorization: app_key
aylien_news_api.configuration.api_key['X-AYLIEN-NewsAPI-Application-Key'] = 'e6f74181cb52f4eeb81f8b7ff79255b4'
#2: aylien_news_api.configuration.api_key['X-AYLIEN-NewsAPI-Application-Key'] = '7db4960c3a727df2249502f592a17167'
#1: aylien_news_api.configuration.api_key['X-AYLIEN-NewsAPI-Application-Key'] = 'dcb76ec967d97f25bd7e54e1a7ad2502'

class Article(object):
    def __init__(self, article_response):
        self.response = article_response
        #print (self.response)

    @property
    def author(self):
        if self.response.author is None:
            return None
        return self.response.author.name

    @property
    def body(self):
        return self.response.body

    @property
    def title(self):
        return self.response.title

    @property
    def source(self):
        if self.response.source is None:
            return None
        return self.response.source.name

    @property
    def url(self):
        if self.response.links is None:
            return None
        return self.response.links.permalink

    def to_dict(self):
        return {'author':self.author, 'body':self.body, 'title':self.title, 
                'source':self.source, 'url':self.url}

class NewsAPI (object):
    def __init__(self):
        self.api_instance = aylien_news_api.DefaultApi()

    def __call__(self, url):
        retval = self._get_article_2(url)
        if retval is None:
            return retval
        return Article(retval)

    def get_an_article(self, domain):
        params = {'language':['en'], 'per_page':1, 'source_domain':[domain]}

        the_story = None
        
        while True:
            try:
                response = self.api_instance.list_stories(**params)
                break
            except ApiException as e:
                if ( e.status == 429 ):
                    print('Usage limit are exceeded. Wating for 60 seconds...')
                    time.sleep(60)
                    continue
                else:
                    print( e)
                    raise

        stories = response.stories
        assert len(stories) > 0

        return Article(stories[0])


    @staticmethod
    def _get_title(url):
        html = urlopen(url)
        soup = BeautifulSoup(html, 'lxml')

        title = soup.head.find('meta', property='og:title')['content']
        return title

    @staticmethod
    def _get_domain(url):
        parsed = urlparse(url).netloc
        if parsed.startswith('www.'):
            parsed = parsed[4:]
        return parsed

    def _get_article_2(self, url):
        title = self._get_title(url)
        domain = self._get_domain(url)
        params = {'language':['en'], 'per_page':10, 'title':title, 'source_domain':[domain]}
        params['cursor'] = '*'

        the_story = None
        done = False

        requests = 0

        while not done and requests < 5:
            try:
                response = self.api_instance.list_stories(**params)
            except ApiException as e:
                if ( e.status == 429 ):
                    print('Usage limit are exceeded. Wating for 60 seconds...')
                    time.sleep(60)
                    continue
                else:
                    print( e)
                    raise

            stories = response.stories
            params['cursor'] = response.next_page_cursor

            if len(stories) == 0:
                break

            requests += 1

            title_parts = set(title.split(' '))
            for story in stories:
                story_title_parts = set(story.title.split(' '))

                AUB = len(title_parts.union(story_title_parts))
                AIB = len(title_parts.intersection(story_title_parts))

                if AIB/AUB > .8:
                    the_story = story
                    done = True
                    break

        return the_story

    def _get_article(self,url):
        title = self._get_title(url)
        domain = self._get_domain(url)

        #opts = {'title':title}
        #print(opts)
        #print(title)

        #r = requests.get(url='https://api.newsapi.aylien.com/api/v1/stories',
        #params={'title':'Kavanaugh AND Accuser AND Opens AND Negotiations AND on AND Testimony AND Next AND Week',
               #'source.domain':'nytimes.com'},
        #headers={'X-AYLIEN-NewsAPI-Application-ID':'0a282753',
                #'X-AYLIEN-NewsAPI-Application-Key':'dcb76ec967d97f25bd7e54e1a7ad2502'})
        params={'title':title}#,
               #'source.domain':domain},
        headers={'X-AYLIEN-NewsAPI-Application-ID':'0a282753',
                'X-AYLIEN-NewsAPI-Application-Key':'dcb76ec967d97f25bd7e54e1a7ad2502'}
        print(params)
        #r = requests.get(url='https://api.newsapi.aylien.com/api/v1/stories',params=params,headers=headers)
        #print(r)

        #response = r.json()

        api_response = self.api_instance.list_stories(**opts)
        print(api_response)
        sys.exit()

        return api_response


if __name__ == '__main__':
    api = NewsAPI()

    for url in ('https://www.nytimes.com/2018/09/19/us/florence-deaths-south-carolina-van.html?partner=rss&emc=rss',
            'https://www.wsj.com/articles/senior-chinese-official-of-uighur-ethnicity-caught-up-in-xis-antigraft-campaign-1537499925?mod=fox_australian',
            'http://www.chicagotribune.com/news/nationworld/politics/ct-mazie-hirono-kavanaugh-critic-20180920-story.html',
            'https://www.breitbart.com/big-government/2018/09/20/pence-accuser-should-be-heard-but-democrats-unfair-to-kavanaugh-and-his-family/?utm_source=feedburner&utm_medium=feed&utm_campaign=Feed%3A+breitbart+%28Breitbart+News%29',
            'https://www.motherjones.com/kevin-drum/2018/09/why-are-there-so-few-blacks-in-clinical-trials-of-cancer-drugs/'):

        art = api(url)
        print(art.title)
        print(art.author)
        print(art.body)
        print()
