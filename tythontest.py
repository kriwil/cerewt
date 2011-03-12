from twython import Twython  

twitter = Twython()  
results = twitter.searchTwitter(q="bert")  

for item in results:
    print item

# More function definitions can be found by reading over twython/twitter_endpoints.py, as well  
# as skimming the source file. Both are kept human-readable, and are pretty well documented or  
# very self documenting.  
