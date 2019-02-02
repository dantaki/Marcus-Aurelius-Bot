#!/usr/bin/env python
'''
Copyright <2019> <Danny Antaki>
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''
__version__='0.0.1'
__usage__="""
   ___  ____  ______   _____   _____  ______   _____   ______
  / _ )/ __ \/_  __/  / _ | | / / _ \/ __/ /  /  _/ | / / __/
 / _  / /_/ / / /    / __ | |/ / , _/ _// /___/ / | |/ /\ \  
/____/\____/ /_/    /_/ |_|___/_/|_/___/____/___/ |___/___/  
-----------------------------------------------------------
Version {}
Author: Danny Antaki dantaki at ucsd dot edu
  python botaur.py  -u <user>  -n <n_tweets>  
	
mining arguments:
  
  -u        user or users separated by commas [required]
  -n        number of tweets to mine          [default: 1]

display arguments:

  -b        number of tweets to display       [default: 3]

optional arguments:

  -h        show this message and exit
	 
""".format(__version__)
from argparse import RawTextHelpFormatter
import tweepy
import argparse,datetime,json,os,random,sys,textwrap,time
def make_line(cha,leng): return ''.join([cha for x in range(0,leng)])
def access_twitter(conf=None):
	"""
	requires a JSON file with your API keys
	logins into the API and returns the tweepy API object
	"""
	with open(conf,'r') as f: data = json.load(f)
	auth = tweepy.OAuthHandler(data['consumer_key'], data['consumer_secret'])
	auth.set_access_token(data['access_token'], data['access_token_secret'])
	api = tweepy.API(auth,wait_on_rate_limit_notify=True)
	return api

####### LOGGING #######
def load_history():
	"""stores all the tweets that the bot tweeted"""
	log=[]
	with open("tweets/marcus_aurelius.log",'r') as f:
		for l in f: log.append(l.rstrip())
	return log
def write_history(tweets):
	"""append to the log file"""
	log = open("tweets/marcus_aurelius.log",'a')
	log.write('{}\n'.format('\n'.join(tweets)))
	log.close()
def check_tweet(tweets,log):
	"""returns 1 if the tweet has been tweeted before"""
	done = 0 
	for t in tweets: 
		if t in log: done=1
	return done
### END OF LOGGING ###

####### RETRIEVE TWEETS #######
def get_tweets(users,api,n_tweets):
	
	usr_twt = {} #dict of the tweetid and user
	# this is used to display the tweet you're replying to

	ln,ts= make_line('_',30),datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
	ofh = 'tweets/maurelius.{}.tweets.txt'.format(ts)
	out = open(ofh,'a')
	sys.stdout.write('\n{}\nCollecting tweets...\n'.format(ln))
	for u in users:
		sys.stdout.write('    {}\n'.format(u))
		# tweets is a list of Status objects (see tweepy api)
		tweets = api.user_timeline(screen_name=u,count=n_tweets,tweet_mode='extended')
		for tw in tweets:
			# store the tweet for later
			if usr_twt.get(tw.id)==None:  usr_twt[tw.id]=[tw.full_text]
			else: usr_twt[tw.id].append(tw.full_text) 

			# write out the tweet. format: tweet ID, username, keyword
			for wrd in tw.full_text.split(' '): out.write('{}\t@{}\t{}\n'.format(tw.id,u,wrd))

	out.close()
	sys.stdout.write('\n{}\n'.format(ln))
	return ofh,usr_twt

def load_tweets(fh):
	"""load your tweets, the tweets matched on keywords"""
	# KW -> ID, TWEET-ID -> [TWEETS], KW -> [TWEET-IDs]
	kw_dict, twt_dict, tid_dict = {}, {}, {}
	with open(fh) as f:
		for l in f:
			ind, kw, _id, tw = l.rstrip().split('\t')
			kw_dict[kw]=_id
			if twt_dict.get(ind)==None: twt_dict[ind]=[tw]
			else: twt_dict[ind].append(tw)
			if tid_dict.get(kw)==None: tid_dict[kw]=[ind]
			else: tid_dict[kw].append(ind) 
	return kw_dict, twt_dict, tid_dict
### END OF RETRIEVE TWEETS ###

####### USER FUNCTIONS #######
def query_tweets(tid):
	ask = input('Please select tweet according to tweet number...\n')
	return ask
def pick_tweets(tid, twt_dict, tw_buff):
	"""
	this shows available tweets that match on a keyword.
	it shows the user the first tw_buff tweets and asks to select one,
	if the user does not input a correct number, then the prompt
	  will ask if to display more tweets. If no, the program exits.
	  If yes, the program will display the next 3 tweets. 
	The process repeats until there are no more tweets to show.

	This function returns the tweet-id (not the tweepy id)
	WARN! bugs abound here, use at your own risk!
	"""
	ln = make_line('_',45)
	sys.stdout.write('\nNumber of Tweets:    {}\nDisplaying first {} tweets...\n\n'.format(len(tid),tw_buff))
	chosen='y'
	for i,e in enumerate(tid):
		if chosen in tid: break
		if i==0: i+=1
		if i%tw_buff==0: # if the tw_buff tweet is reached
			chosen = query_tweets(tid)
			if chosen not in tid:
				ask = input('\n{} Not a correct tweet number.\n    Display more tweets? [y/n]\n'.format(chosen))
				if ask != 'y': 
					sys.stdout.write('\nExiting!\n')
					sys.exit(0)
		tws = ' * '.join(twt_dict[e]) # join replies that span 2 tweets separated by a star
		sys.stdout.write('\n{}\n{}\n{}\n{}\n'.format(ln,e,textwrap.fill(tws,45),ln))
	if chosen not in tid: chosen = query_tweets(tid)
	if chosen not in tid: 
		sys.stdout.write('{} Not a correct tweet number.\nExiting!\n'.format(chosen))
		sys.exit(0)
	return chosen
def show_keywords(kws):
	"""function to ask the user to select a keyword. this might be buggy"""
	ln,qn = make_line('_',60),make_line('_',40)
	sys.stdout.write('KEYWORDS\n{}\n{}\n{}\n'.format(ln,textwrap.fill(' * '.join(kws),60),ln))
	chosen_kw = input("\n{}\nPick a keyword... \n{}\n".format(qn,qn))
	if chosen_kw not in kws:
		sys.stderr.write('ERROR: {} is not a keyword!\nExiting!\n'.format(chosen_kw))
		sys.exit(1)
	return chosen_kw
###  END OF USER FUNCTIONS ###

def tweet_it(tweets,_id):
	"""tweet the damn tweet already!"""
	ln = make_line('_',45)
	write_history(tweets)
	sys.stdout.write('\n{}\nT W E E T I N G ...\n'.format(ln,ln))
	last_status=None # variable to store the tweepy-id if you need to chain a tweet
	for tweet in tweets: 
		sys.stdout.write('\n{}\n{}\n{}\n'.format(ln,textwrap.fill(tweet,45),ln))
		if last_status == None: # the _id variable below is the tweepy-id you're replying to
			last_status = api.update_status(status=tweet,in_reply_to_status_id=_id) 
		else: # the last_status.id is the tweepy-id of the previous tweet you made
			last_status = api.update_status(status=tweet,in_reply_to_status_id=last_status.id)
	sys.stdout.write('\n')

#### M A I N  L O O P ####
if __name__ == "__main__":
	parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter, usage=__usage__, add_help=False)
	mine_args, dis_args, opt_args = parser.add_argument_group('mining arguments'), parser.add_argument_group('display arguments'), parser.add_argument_group('optional arguments')
	mine_args.add_argument('-u',type=str,default=None,required=True)
	mine_args.add_argument('-n',type=int,default=1,required=False)
	dis_args.add_argument('-b',type=int,default=3,required=False)
	opt_args.add_argument('-h', '-help', required=False, action="store_true", default=False) 
	args = parser.parse_args()
	users, n_tweets = args.u.split(','), args.n
	tw_buff = args.b
	_help = args.h
	if (_help==True or len(sys.argv)==1):
		sys.stdout.write(__usage__)
		sys.exit(0)
	ln,qn = make_line('-',60),make_line('_',40)
	log = load_history()
	api = access_twitter('tweet.json')
	# get the tweets from users
	ofh,usr_twt = get_tweets(users,api,n_tweets)
	sys.stdout.write('\n{}\n            M  E  D  I  T  A  T  I  N  G             \n{}\n'.format(ln,ln))
	t = os.system("perl parse_tweets.pl {}".format(ofh))
	twts = ofh.replace(".txt",'.meditations.txt')
	# get tweets
	kw_dict, twt_dict, tid_dict = load_tweets(twts)
	kws = sorted(list(set(kw_dict.keys())))
	# print keywords
	chosen_kw = show_keywords(kws)
	while kw_dict.get(chosen_kw)!=None:
		sys.stdout.write('\n{}\nResponding to ...\n\n{}\n'.format(qn,textwrap.fill(''.join(usr_twt[int(kw_dict[chosen_kw])]),30)))
		cont = input("\n\nContinue? [y/n]\n{}\n".format(qn))
		while cont=='n':
			chosen_kw = show_keywords(kws)
			sys.stdout.write('\n{}\nResponding to ...\n{}\n{}\n'.format(qn,textwrap.fill(''.join(usr_twt[int(kw_dict[chosen_kw])]),30),qn))
			cont = input("\n{}\nContinue? [y/n]\n{}\n".format(qn,qn))

		# get tweets from user
		tweets = twt_dict[pick_tweets(sorted(set(tid_dict[chosen_kw])),twt_dict,tw_buff)]
		# check if in history
		if check_tweet(tweets,log)==1:
			sys.stdout.write('ERROR: {}\n\nhas been tweeted before!\nSkipping... '.format(textwrap.fill(' '.join(tweets),30)))
		else: tweet_it(tweets,kw_dict[chosen_kw]) # troll away
		# keep on tweeting
		ask = input('\n{}\nTweet again with the same keyword? [y/n]\n{}\n'.format(qn,qn))
		while ask=='y':
			tweets = twt_dict[pick_tweets(sorted(set(tid_dict[chosen_kw])),twt_dict,tw_buff)]
			if check_tweet(tweets,log)==1:
				sys.stdout.write('ERROR: {}\n\nhas been tweeted before!\nSkipping... '.format(textwrap.fill(' '.join(tweets),30)))
			else: tweet_it(tweets,kw_dict[chosen_kw])
			ask = input('\n{}\nTweet again with the same keyword? [y/n]\n{}\n'.format(qn,qn))
		# ask for a new keyword 
		ask = input('\n{}\nPick a new keyword?  [y/n]\n{}\n'.format(qn,qn))
		if ask =='y':
			chosen_kw=show_keywords(kws)
		else: 
			sys.stdout.write('\nExiting!\n')
			sys.exit(0)