import nltk
from collections import defaultdict
import string
from locale import str
import sys
import random


if len(sys.argv) != 3:
    print '{ "results" : "error"}'
    sys.exit()



def get_words_in_tweets(tweets):
    all_words = []
    for (words, sentiment) in tweets:
      all_words.extend(words)
    return all_words


def get_word_features(wordlist):
    wordlist = nltk.FreqDist(wordlist)
    word_features = wordlist.keys()
    return word_features


def extract_features(document):
    document_words = set(document)
    features = {}
    for word in word_features:
        features['contains(%s)' % word] = (word in document_words)
    return features


pos_tweets = []
neg_tweets = []

with file ('positive.csv', 'rt') as f:
   for line in f.readlines():
       pos_tweets.append((line.replace("\n",""), 'positive'))

 
with file ('negative.csv', 'rt') as f:
   for line in f.readlines():
       neg_tweets.append((line.replace("\n",""), 'negative'))



#there will likely always be more positve than negative
#randomly pick the postive ones to use
if pos_tweets > neg_tweets:
    
    
    new_pos_tweets = []
    
    for i in range(len(neg_tweets)):
    
        
        
        
        random_pos = pos_tweets[random.randrange(0,len(pos_tweets))]
        new_pos_tweets.append(random_pos)
        

            
             
    pos_tweets = new_pos_tweets
    



tweets = []
exclude = set(string.punctuation)


for (words, sentiment) in pos_tweets + neg_tweets:
     
    words_filtered = []
    for item in nltk.bigrams(words.split()):
       words_filtered.append(' '.join(item).lower())
         
    if len(words_filtered) > 0:
        tweets.append((words_filtered, sentiment))
    

word_features = get_word_features(get_words_in_tweets(tweets))
training_set = nltk.classify.apply_features(extract_features, tweets)
classifier = nltk.NaiveBayesClassifier.train(training_set)


tweet = sys.argv[2].lower().replace('%20',' ')

cmd = sys.argv[1].lower()


#tweet = "is identical to fail to account for the original person and the other not?"

tweet = tweet.replace(".","").replace("?","").replace(",","").replace(";","").replace(":","").replace("!","").replace('"',"").replace("'","")

tweet_bigram = []

for item in nltk.bigrams(tweet.split()):
   tweet_bigram.append(' '.join(item).lower())


probdist = classifier.prob_classify(extract_features(tweet_bigram))
results  = classifier.classify(extract_features(tweet_bigram))


#print probdist.prob('positive')

#print probdist.prob('negative')

if (cmd == 'analyze'):
    
    print '{ "results" : "' + results + '", "positive" : "' + "{0:.10f}".format(probdist.prob('positive')) + '", "negative" : "' + "{0:.10f}".format(probdist.prob('negative')) + '"}'
    

elif (cmd == 'features'):

    print '{ "results" : "'
    print classifier.show_most_informative_features(32)
    print '"}'



