#!/usr/bin/perl
use strict; use warnings;
# list of keywords to search for in text
undef my @keys; undef my %id; undef my %usr;
open IN, "$ARGV[0]";
while(<IN>){ chomp; 
	my @r = split /\t/, $_;
	next if(scalar(@r)!=3);
	my ($id,$usr, $kw)= @r;
	push @keys, $kw; $id{$kw}=$id; $usr{$kw}=$usr; } close IN;
# load mask of words to omit
undef my %mask;
open IN, "word_mask.txt"; while(<IN>){ chomp; my @a = split / /, $_; foreach my $w (@a){ $mask{$w}++; }} 
close IN;

# load the text into a list
undef my @scroll;
open IN, "scrolls/meditations_marcus_aurelius.txt";
while(<IN>){ chomp; push @scroll, $_; } close IN; 
my $scroll = join " ",@scroll;
# remove all chapter numbers
$scroll =~ s/[0-9]\.//g; $scroll =~ s/[0-9]//g;
my $ind = 0; #unique id

# split by lower-case letter and period (like the end of a sentence)
# the decorators are to retain the delimiter
my @text = split /(?<=[a-z]\.)/, $scroll; 

my $SUB_TWT_LEN = 200; # length of a sub-tweet, if the sentence is too long
my $MAX_TWEET = 1; # maximum number of tweets in a thread
my $SIG = " - Meditations by M.Aurelius"; # signature

my $ofh = $ARGV[0]; $ofh =~ s/\.txt/\.meditations\.txt/;
open OUT, ">$ofh";
foreach my $KW (@keys){
	my $kw = $KW; # save the origin for the id hash
	$kw =~ s/\(//g; $kw =~ s/\)//g;
	$kw =~ s/[0-9\?\;\,\.\'\"\$\%\@\#\:\!\&\*\“\”]//g; #remove punctuation
	next if($kw eq "");
	next if(exists $mask{lc($kw)}); #skip words in the mask
	next if($kw =~ /http/);

	undef my %done; # dict to keep track of processed tweets
	my $tkw = $kw; # string with a hashtag
	$tkw = "#".$kw if($kw !~ /^\#/); #add hashtag if not there

	foreach my $s (@text){
		next if($s =~ /END OF THE/); next if($s =~ /BOOK /); # skip these text
		# if we match on the keyword
		if($s =~ /\ $kw /i) {
			# remove leading whitespace until it's gone
			do {$s =~ s/^ //; } until ($s !~ /^ /); 
			# remove trailing whitespace until it's gone
			do {$s =~ s/ $//; } until ($s !~ /\ $/);
			$s =~ s/$kw/$tkw/i; # replace the keyword with the hashtag
			$s = $s . $SIG if($s !~ /$SIG$/); # add a signature 
			$s = "$usr{$KW} ".$s if($s !~ /^$usr{$KW}/); # add the user
			next if(exists $done{$s}); # skip if already processed
			# if the tweet is too long
			if (length($s) > 240){ 
				undef my @tweets; 
				my @t = split / /, $s; # split by words
				my $t = shift @t; # take the first word
				
				# add sub-tweets to @tweets
				do{  # if the length of the word and next word is greater than the sub-tweet length
					if(length($t)+length($t[0]) > $SUB_TWT_LEN){ 
						push @tweets, $t; # push the word(s) to tweets
						$t = shift @t; # get the next word
				
					# if the length is less than the max sub-tweet length: concat the two words
					} else { my $tt = shift @t; $t=$t." ".$tt; } 
				} until(scalar(@t)==0); # do this until all words are processed
				push @tweets, $t; 

				# compare the last two sub-tweets, if they fit within 240 characters, then join them
				my $last = pop @tweets; 
				if(length($last)+length($tweets[-1]) < 239) { my $tt = pop @tweets; push @tweets, "$last $tt"; }
				else { push @tweets, $last;}  # if not then push the last tweet back

				# print the tweets! 
				next if(scalar(@tweets)>$MAX_TWEET); #skip long tweets
				foreach my $tweet (@tweets) { print OUT "$ind\t$kw\t$id{$KW}\t$tweet\n"; }
				$done{$s}++; $ind++; 
			} 
			else { print OUT "$ind\t$kw\t$id{$KW}\t$s\n"; $done{$s}++; $ind++; }	
		} 
	}
}
