#!/usr/bin/env python
import tweepy
import datetime,json,os,random,sys,textwrap,time
def access_twitter(conf=None):
	with open(conf,'r') as f: data = json.load(f)
	auth = tweepy.OAuthHandler(data['consumer_key'], data['consumer_secret'])
	auth.set_access_token(data['access_token'], data['access_token_secret'])
	api = tweepy.API(auth,wait_on_rate_limit_notify=True)
	return api
def load_history():
	log=[]
	with open("tweets/marcus_aurelius.log",'r') as f:
		for l in f: log.append(l.rstrip())
	return log
def write_history(tweets):
	log = open("tweets/marcus_aurelius.log",'a')
	log.write('{}\n'.format('\n'.join(tweets)))
	log.close()
def make_line(cha,leng): return ''.join([cha for x in range(0,leng)])
def get_tweets(users,api):
	usr_twt = {}
	ln = make_line('_',30)
	ts = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
	ofh = 'tweets/maurelius.{}.tweets.txt'.format(ts)
	out = open(ofh,'a')
	sys.stdout.write('\n{}\nCollecting tweets...\n'.format(ln))
	for u in users:
		sys.stdout.write('    {}\n'.format(u))
		tweets = api.user_timeline(screen_name=u,count=10,tweet_mode='extended')
		for tw in tweets:
			if usr_twt.get(tw.id)==None:  usr_twt[tw.id]=[tw.full_text]
			else: usr_twt[tw.id].append(tw.full_text) 
			for wrd in tw.full_text.split(' '): out.write('{}\t@{}\t{}\n'.format(tw.id,u,wrd))
	out.close()
	sys.stdout.write('\n{}\n'.format(ln))
	return ofh,usr_twt
def load_tweets(fh):
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
def query_tweets(tid):
	ask = input('Please select tweet according to tweet number...\n')
	return ask
def pick_tweets(tid, twt_dict):
	ln = make_line('_',45)
	sys.stdout.write('\nNumber of Tweets:    {}\nDisplaying first 3 tweets...\n\n'.format(len(tid)))
	chosen='y'
	for i,e in enumerate(tid):
		if chosen in tid: break
		if i==0: i+=1
		if i%3==0: 
			chosen = query_tweets(tid)
			if chosen not in tid:
				ask = input('\n{} Not a correct tweet number.\n    Display more tweets? [y/n]\n'.format(chosen))
				if ask != 'y': 
					sys.stdout.write('\nExiting!\n')
					sys.exit(0)
		tws = ' * '.join(twt_dict[e])
		sys.stdout.write('\n{}\n{}\n{}\n{}\n'.format(ln,e,textwrap.fill(tws,45),ln))
	if chosen not in tid: chosen = query_tweets(tid)
	if chosen not in tid: 
		sys.stdout.write('{} Not a correct tweet number.\nExiting!\n'.format(chosen))
		sys.exit(0)
	return chosen
def check_tweet(tweets,log):
	done = 0 
	for t in tweets: 
		if t in log: done=1
	return done
def show_keywords(kws):
	ln,qn = make_line('_',60),make_line('_',40)
	sys.stdout.write('KEYWORDS\n{}\n{}\n{}\n'.format(ln,textwrap.fill(' * '.join(kws),60),ln))
	chosen_kw = input("\n{}\nPick a keyword... \n{}\n".format(qn,qn))
	if chosen_kw not in kws:
		sys.stderr.write('ERROR: {} is not a keyword!\nExiting!\n'.format(chosen_kw))
		sys.exit(1)
	return chosen_kw
def tweet_it(tweets,_id):
	ln = make_line('_',45)
	write_history(tweets)
	sys.stdout.write('\n{}\nT W E E T I N G ...\n'.format(ln,ln))
	last_status=None
	for tweet in tweets: 
		sys.stdout.write('\n{}\n{}\n{}\n'.format(ln,textwrap.fill(tweet,45),ln))
		if last_status == None:
			last_status = api.update_status(status=tweet,in_reply_to_status_id=_id)
		else:
			last_status = api.update_status(status=tweet,in_reply_to_status_id=last_status.id)
	sys.stdout.write('\n')
if __name__ == "__main__":
	ln = make_line('-',60)
	qn = make_line('_',40)
	log = load_history()
	api = access_twitter('tweet.json')
	users = [
		#'realDonaldTrump',
		#'AOC',
		'DonaldJTrumpJr',
		#'TuckerCarlson',
		#'TeamTrump'
		#'RealJamesWoods',
		]
	# get the tweets from users
	ofh,usr_twt = get_tweets(users,api)
	sys.stdout.write('\n{}\n            M E D I T A T I N G            \n{}\n'.format(ln,ln))
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
		tweets = twt_dict[pick_tweets(sorted(set(tid_dict[chosen_kw])),twt_dict)]
		# check if in history
		if check_tweet(tweets,log)==1:
			sys.stdout.write('ERROR: {}\n\nhas been tweeted before!\nSkipping... '.format(textwrap.fill(' '.join(tweets),30)))
		else: tweet_it(tweets,kw_dict[chosen_kw]) # troll away
		# keep on tweeting
		ask = input('\n{}\nTweet again with the same keyword? [y/n]\n{}\n'.format(qn,qn))
		while ask=='y':
			tweets = twt_dict[pick_tweets(sorted(set(tid_dict[chosen_kw])),twt_dict)]
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