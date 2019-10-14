import sys
import time
import pickle
import collections
from nltk import FreqDist


class Utils:
	@staticmethod
	def load_words_list(filename):
		with open(filename, 'r') as fin:
			words = [line.strip().split()[1] for line in fin]
		# end with
		return words
	# end def

	@staticmethod
	def parse_classification_configuration(cfg_filename):
		configuration = []
		with open(cfg_filename, 'r') as fin:
			for line in fin:
				if line.startswith("#") or not line.strip(): continue
				configuration.append(label(line.split()[0], line.split()[1], line.split()[2]))
			# end for
		# end with
		return configuration
	# end def

	@staticmethod
	def divide_into_chunks(configuration):
		labels = []
		text_chunks = []

		for entry in configuration:
			print("loading", entry.chunks, "chunks from", entry.datafile)
			with open(entry.datafile, 'r') as fin:
				text = fin.read().strip()
				tokens = text.split()

				processed_chunks = 0
				for i in range(0, len(tokens), CHUNK_SIZE):
					text_chunks.append(' '.join(tokens[i:i + CHUNK_SIZE]).lower())
					labels.append(entry.name)
					processed_chunks += 1

					if processed_chunks == int(entry.chunks):
						break
					# end if
				# end for
			# end with
		# end for
		return text_chunks, labels
	# end def

# end class


class Classification:

	@staticmethod
	def create_features_map(cfg_filename, vocab_filename):
		start = time.clock()
		configuration = Utils.parse_classification_configuration(cfg_filename)
		text_chunks, labels = Utils.divide_into_chunks(configuration)

		countries = [entry.name for entry in configuration]

		dictionary = {}
		words_list = Utils.load_words_list(vocab_filename)
		for country, chunk in zip(countries, text_chunks):
			dcountry = {}
			dist = FreqDist(chunk.split())
			for word in words_list:
				dcountry[word] = dist[word]
			# end for
			dictionary[country] = dcountry
		# end for

		with open('vocab.countries.pkl', 'wb') as fout:
			pickle.dump(dictionary, fout, pickle.HIGHEST_PROTOCOL)
		# end with

		print('time:', '{0:.3f}'.format(time.clock() - start))
	# end def

# end class


CHUNK_SIZE = 2500000
label = collections.namedtuple('label', ['datafile', 'name', 'chunks'])
VOCAB_FILENAME = 'vocabulary.100.dat'

# invocation: "python extract_word_count.py data.reddit.voc.cfg"

if __name__ == '__main__':

	cl = Classification()
	cl.create_features_map(sys.argv[1], VOCAB_FILENAME)


# end if
