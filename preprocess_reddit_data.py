import os
import glob
import codecs
from polyglot.detect import Detector


class Parsing:
	@staticmethod
	def is_english_sentence(text):
		'''
		detects the language of a given text (sentence)
		:param text:
		:return: boolean
		'''
		try:
			detector = Detector(text)
		except:
			# the detector could not identify the language
			# typically extremely short non-alphabetic sentences
			return False
		# end try
		language = detector.languages[0].name
		return language == 'English'
	# end def

	@staticmethod
	def is_web_link(token):
		'''
		check if a given token is weblink, subreddit or username
		:param token:
		:return: boolean
		'''
		# url or subreddit (r/<subreddit>) or user id (u/<user>)
		return token.startswith('http:') or token.startswith('https:') or \
			   token.startswith('r/') or token.startswith('u/')
	# end def

	@staticmethod
	def perform_url_cleanup(input_dir):
		'''
		traverse all files in the input directory and sustitute links with 'URL' token
		:param input_dir:
		:return:
		'''
		for filename in sorted(glob.glob(input_dir + '*')): # can specify pattern
			outfile = filename + '.out'

			with codecs.open(filename, 'r', 'utf-8') as fin, codecs.open(outfile, 'w', 'utf-8') as fout:
				print('processing', filename)
				for line in fin:
					# replace all urls with 'URL' token
					tokens = [token if not Parsing.is_web_link(token) else 'URL' for token in line.strip().split()]
					fout.write(' '.join(tokens) + '\n') # write down the line
				# end for
			# end with
		# end for
	# end def

	@staticmethod
	def find_2nd_occurrence(text, substr):
		'''
		find the second occurrence of a pattern in a string (if exists)
		:param text: string to search
		:param substr: pattern to find
		:return: index
		'''
		return text.find(substr, text.find(substr) + 1)
	# end def
# end class


class SimpleTrueCasing:
	@staticmethod
	def true_case(input_dir):
		'''
		apply tru case on the reddit text -- lower, upper, or c title case
		the case is determined according the maximum likelihood of a trigram, where the token is in the middle
		:param input_dir:
		:return:
		'''
		trigram_freq, unigram_freq = Frequency.load_frequencies()
		for filename in sorted(glob.glob(input_dir + '*')):
			outfile = filename + '.tc'  # true case

			with codecs.open(filename, 'r', 'utf-8') as fin, codecs.open(outfile, 'w', 'utf-8') as fout:
				print('processing', filename)
				for line in fin:
					line = line.strip()
					if len(line.split()) == 1 and line.islower() and line.isalpha():
						fout.write(line.capitalize() + '\n')
						continue
					# end if

					out_tokens = []
					split_line = line.split()
					for i, token in enumerate(split_line):
						# if it's first or last token
						if i == 0 or i == len(split_line) - 1 or not token.islower():
							out_tokens.append(token)
							continue
						# end if

						# we have left- and right-tokens, check trigram frequency
						f_current = int(trigram_freq.get(' '.join([split_line[i - 1], token, split_line[i + 1]]), 0))
						f_capitalize = int(trigram_freq.get(' '.join([split_line[i - 1], token.capitalize(), split_line[i + 1]]), 0))
						f_upper = int(trigram_freq.get(' '.join([split_line[i - 1], token.upper(), split_line[i + 1]]), 0))
						f_max = max([f_current, f_capitalize, f_upper])

						if f_max == 0:  # no trigram containing the token found, fall back to unigrams
							f_current = int(unigram_freq.get(token, 0))
							f_capitalize = int(unigram_freq.get(token.capitalize(), 0))
							f_upper = int(unigram_freq.get(token.upper(), 0))
							f_max = max([f_current, f_capitalize, f_upper])
						# end if

						if f_max == f_current:
							out_tokens.append(token)
							continue
						elif f_max == f_capitalize:
							out_tokens.append(token.capitalize())
							continue
						else:  # f_max == f_upper
							out_tokens.append(token.upper())
							continue
						# end if
					# end for
					fout.write(' '.join(out_tokens) + '\n')
				# end for
			# end with
		# end for
	# end def
# end class


class Frequency:
	@staticmethod
	def load_frequencies():
		'''
		load unigram and trigram frequencies from the COCA ngrams data
		freely downloadable at https://www.ngrams.info/download_coca.asp
		:return:
		'''
		trigram_freq = {}
		unigram_freq = {}
		with codecs.open(NGRAMS_DIR + 'w3.txt', 'r', 'utf-8') as fin:
			for line in fin:
				fields = line.strip().split()
				if len(fields) < 4: continue  # we expect 4 fields
				trigram_freq[' '.join(fields[1:4])] = fields[0]

				for i in range(1, 4):
					unigram_freq[fields[i]] = unigram_freq.get(fields[i], 0) + 1
				# end for
			# enf for
		# end with

		with codecs.open(NGRAMS_DIR + 'w2.txt', 'r', 'utf-8') as fin:
			for line in fin:
				fields = line.strip().split()
				if len(fields) < 3: continue  # we expect 3 fields
				for i in range(1, 3):
					unigram_freq[fields[i]] = unigram_freq.get(fields[i], 0) + 1
				# end for
			# enf for
		# end with
		return trigram_freq, unigram_freq
	# end def
# end class


class Utils:
	@staticmethod
	def extract_european_data(input_dir_name, out_dir_name):
		'''
		extract posts and comments submitted to the european subreddits
		:param input_dir_name: input files dir
		:param out_dir_name: output files dir
		:return:
		'''
		for filename in sorted(glob.glob(input_dir_name + '*.tok')):
			outfile = out_dir_name + os.path.basename(filename)

			with codecs.open(filename, 'r', 'utf-8') as fin, codecs.open(outfile, 'w', 'utf-8') as fout:
				print('processing', filename)
				for line in fin:
					start = Parsing.find_2nd_occurrence(line.strip(), '[')
					end = Parsing.find_2nd_occurrence(line.strip(), ']')
					subreddit = line[start + 1:end].strip()
					# print(subreddit)

					if subreddit not in EUROPEAN_SUBREDDITS: continue
					text = line.strip()[end + 2:]
					fout.write(text + '\n')
				# end for
			# end with
		# end for
	# end def

	@staticmethod
	def perform_cleanup(input_dir):
		for filename in sorted(glob.glob(input_dir + 'reddit.*.500K')):
			outfile = filename + '.nometa'

			with codecs.open(filename, 'r', 'utf-8') as fin, codecs.open(outfile, 'w', 'utf-8') as fout:
				print('processing', filename)
				for line in fin:
					# raw text without metadata
					index = Parsing.find_2nd_occurrence(line.strip(), ']')

					text = line.strip()[index + 2:]
					metadata = line.strip()[:index + 1]
					metadata = metadata.replace('[ ', '[').replace(' ]', ']')  # remove metadata spaces
					# two metadata attributes and single non-alphabetical word
					if len(text.split()) == 1 and not (text.isalpha()): continue
					if not (Parsing.is_english_sentence(text)): continue
					# fout.write(metadata + ' ' + text + '\n')
					fout.write(text + '\n')

				# end for
			# end with
		# end for
	# end def
# end class


class AbstactRepresentation:
	@staticmethod
	def remove_short_sentences_and_named_entities(nlp, input_dir):
		'''

		:param nlp: the spacy nlp pipeline object
		:param input_dir: input files dir to traverse
		:return:
		'''
		for filename in sorted(glob.glob(input_dir + 'reddit.V*.nometa.tc')):
			outfile = filename + '.trial'

			count = 0
			with codecs.open(filename, 'r', 'utf-8') as fin, codecs.open(outfile, 'w', 'utf-8') as fout:
				print('processing', filename)
				for line in fin:
					entity2label = {}
					line_with_entities = []

					line = line.strip()
					sentence = nlp(line) # spacy pipeline invocation
					for ent in sentence.ents: entity2label[ent.text] = ent.label_

					prev_end = 0
					for ent in sentence.ents:
						line_with_entities.append(line[prev_end:ent.start_char])
						line_with_entities.append(ent.label_)
						prev_end = ent.end_char
					# end for

					line_with_entities.append(line[prev_end:])
					line_with_entities = (' '.join(line_with_entities)).strip()

					outline = []
					for token in line_with_entities.split():
						if token in entity2label.values(): # named entity
							outline.append(token)
						elif token.isalpha() and token not in nlp.vocab: # not in English vocabulary
							outline.append('FW')
						elif Parsing.is_web_link(token): # web link, r/<subreddit> or u/<username>
							outline.append('URL')
						else: # English word, not named entity
							outline.append(token.lower())
						# end if
					# end for

					fout.write(' '.join(outline) + '\n')

					if count % 10000 == 0: print(count)
					count += 1
				# end for
			# end with
		# end for
	# end def

	@staticmethod
	def pos_tag(nlp, input_dir):
		'''
		annotate text for part-of-speech
		:param nlp: the spacy nlp pipeline object
		:param input_dir: input files dir to traverse
		:return:
		'''
		for filename in sorted(glob.glob(input_dir + '*')):
			outfile = filename + '.pos'

			count = 0
			with codecs.open(filename, 'r', 'utf-8') as fin, codecs.open(outfile, 'w', 'utf-8') as fout:
				print('processing', filename)
				for line in fin:
					outline = []
					sentence = nlp(line.strip())  # spacy pipeline
					for token in sentence: outline.append(token.text + '_' + token.tag_)
					fout.write(' '.join(outline) + '\n')

					if count % 10000 == 0: print(count)
					count += 1
				# end for
			# end with
		# end for
	# end def
# end class


if __name__ == '__main__':

	# https://www.ngrams.info/download_coca.asp
	NGRAMS_DIR = 'directory with n-gram frequencies, e.g., downloaded from COCA'
	EUROPEAN_SUBREDDITS = ['europe', 'AskEurope', 'EuropeanCulture', 'EuropeanFederalists', 'Eurosceptics']

	processor = AbstactRepresentation()

	import spacy
	# should work best for NER (https://spacy.io/usage/v2)
	input_dir = 'directory with input files, the data is available at http://cl.haifa.ac.il/projects/l2'
	nlp = spacy.load('en_core_web_lg', disable=['parser', 'tagger'])
	processor.remove_short_sentences_and_named_entities(nlp, input_dir)

	# refer to https://spacy.io/usage/models for models
	#nlp = spacy.load('en_core_web_sm', disable=['parser', 'entity'])
	#input_dir = 'directory with input files, the data is available at http://cl.haifa.ac.il/projects/l2'
	#pos_tag(nlp, input_dir)

	print('finished')

# end if
