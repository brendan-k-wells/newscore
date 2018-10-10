from flask import render_template
from flask import request
from newscore import app
from .news_api import NewsAPI
from .score import Score
from flask import Markup

import html
import datetime


api = NewsAPI()
score_gen = Score()


@app.route('/')
@app.route('/index')
def index():
    def linkify(ex_dict):
        ex_dict['link'] = "http://newscore.ink/go?url={}&push=".format(html.escape(ex_dict['url']))
    example = [None]*3
    example[0] = api.get_an_article('washingtonpost.com').to_dict()
    linkify(example[0])
    example[1] = api.get_an_article('chicagotribune.com').to_dict()
    linkify(example[1])
    example[2] = api.get_an_article('eastbaytimes.com').to_dict()
    linkify(example[2])
    print (example)


    return render_template('master.html', placeholder_text='Enter a URL', example=example)


@app.route('/go')
def go():
    try:
        url = request.args.get('url')
        with open('logfile.txt', 'a') as logfile:
            logfile.write('{}:{}\n'.format(datetime.datetime.now(), url))
        article = api(url)
        assert article is not None

        article_dict = article.to_dict()
        article_dict['url'] = url
        
        score_val = score_gen.score(article_dict['body'])
        score_text = score_gen.score_to_text(score_val)
        score_words = score_gen.words(article_dict['body'])
        

        score = {'number': '{:.2f}'.format(score_val), 'text': score_text}

        article_dict['body'] = _process_body(article_dict['body'], score_words)
        with open('logfile.txt', 'a') as logfile:
            logfile.write('\t{}:{}\n'.format(datetime.datetime.now(), score['number']))

        return render_template('go.html', article=article_dict, score=score, placeholder_text = url)
    except: 
        return render_template('error.html', url=url)


from spacy.lang.en import English
parser = English()

def _process_body(body, words):
    tokens = parser(body)
    cur_str = ''
    for token in tokens:
        cur_text = token.text_with_ws
        cur_token = token.lemma_.lower().strip()
        if cur_token in words[0]:
            cur_text = cur_text.replace(cur_text.strip(), '<span class="objective">{}</span>'.format(cur_text.strip()))
        elif cur_token in words[1]:
            cur_text = cur_text.replace(cur_text.strip(), '<span class="opinion">{}</span>'.format(cur_text.strip()))
        cur_str += cur_text
    return Markup(r'<p>'+r'<p>'.join(cur_str.split('\n')))
