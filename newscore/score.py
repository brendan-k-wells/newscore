import pickle
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
import os
from sklearn.preprocessing import normalize
import spacy
spacy.load('en')
from spacy.lang.en import English
parser = English()

class Score (object):
    def __init__(self):
        with open('newscore/data.pkl', 'rb') as infile:
            self.corpus = pickle.load(infile)
            self.nf = pickle.load(infile)
            self.no = pickle.load(infile)
            self.X = pickle.load(infile)



        vect = CountVectorizer()
        vect.set_params(tokenizer=self._tokenizeText)
        vect.set_params(ngram_range=(1,1))
        vect.set_params(min_df=3)
        
        print('Loading corpus')
        self.vect = vect.fit(self.corpus)
        print('Done loading corpus')

    @staticmethod
    def _tokenizeText(sample):
        #print( type(sample))
        SYMBOLS = ['\n','']

        tokens = parser(sample)
        lemmas = []
        for tok in tokens:
            lemmas.append(tok.lemma_.lower().strip() if tok.lemma_ != "-PRON-" else tok.lower_)
        tokens = lemmas
        tokens = [tok for tok in tokens if tok not in SYMBOLS]

        return tokens

    def _get_vec(self, text):
        vec = self.vect.transform([text])
        vec = normalize(vec, norm='l2')
        return vec

    def _get_dist(self, vec):
        fact_dist = np.sort((np.dot(vec,self.X[:self.nf,:].T)).T.toarray())
        op_dist = np.sort((np.dot(vec,self.X[self.nf:self.nf+self.no,:].T)).T.toarray())

        fact_inv_dist = 1/np.power(fact_dist[fact_dist>0],4)
        op_inv_dist = 1/np.power(op_dist[op_dist>0],4)

        return fact_inv_dist, op_inv_dist

    def score(self,text):
        vec = self._get_vec(text)
        fact_inv_dist, op_inv_dist = map(np.sum,self._get_dist(vec))

        measure = ((fact_inv_dist)/(op_inv_dist+fact_inv_dist))
        #measure = self._scale((fact_inv_dist)/(op_inv_dist+fact_inv_dist))

        return measure*100

    def words(self, text):
        vec = self._get_vec(text)
        fact_inv_dist, op_inv_dist = self._get_dist(vec)

        fact_average_scores = np.mean(fact_inv_dist.reshape((-1,1)) * self.X[:self.nf,:].toarray(),axis=0) \
                - np.mean(op_inv_dist.reshape((-1,1)) * self.X[self.nf:self.nf+self.no,:].toarray(),axis=0)

        diff_keys = zip(fact_average_scores,self.vect.get_feature_names())
        diff_keys = sorted(diff_keys, key=lambda x: x[0], reverse=True)

        top = map(lambda x:x[1], diff_keys[:10])
        bottom = map(lambda x:x[1], diff_keys[-10:])

        return list(top), list(bottom)


    @staticmethod
    def _scale(value):
        value2 = (value-.2) * 0.6/0.3 + .2
        if value2 > 1:
            return 1
        if value2 < 0:
            return 0
        return value2



    def score_to_text(self,measure):
        if measure < 20:
            return 'strongly opinion'
        elif measure < 40:
            return 'likely opinion'
        elif measure < 60:
            return 'some opinion'
        elif measure < 80:
            return 'mostly objective'
        else:
            return 'objective'

