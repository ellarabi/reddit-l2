import sys, math
import numpy as np
import multiprocessing as mp
import itertools
import pickle

from numpy import linalg as LA
from scipy.spatial.distance import cityblock


def load_obj(name):
	with open(name, 'rb') as fin: return pickle.load(fin)
# end def


def get_facets(filename):
	facets = {}
	file = open(filename)

	for line in file:
		cols = line.rstrip().split(" ")
		facets[cols[0]] = 1
	# end for
	file.close()

	# don't count the base facet
	del facets["MAIN"]

	return facets.keys()
# end def


def normalize_dist(freq_dist):
	norm_freq_dist = {}
	dmin = min([freq_dist[key] for key in freq_dist.keys()])
	dmax = max([freq_dist[key] for key in freq_dist.keys()])

	for key in freq_dist.keys():
		norm_freq_dist[key] = (freq_dist[key]-dmin)/(dmax-dmin)
	# end for

	return norm_freq_dist
# end def


def normalize(embeddings):
	for name in embeddings:
		for word in embeddings[name]:
			a = embeddings[name][word]
			norm = LA.norm(a, 2)
			a /= norm

			embeddings[name][word] = a
		# end for
	# end for
# end def


def parse_embeddings(filename):
	embeddings = {}
	file = open(filename)

	facets = get_facets(filename)
	# if you want to only consider a few metadata facets and not all, do that below
	#facets = ['France', 'Italy']

	for facet in facets:
		embeddings[facet] = {}
	# end for

	for line in file:
		cols = line.rstrip().split(" ")
		if len(cols) < 10: continue # corrupted line
		facet = cols[0]

		if facet != "MAIN" and facet not in embeddings: continue

		word = cols[1]
		vals = cols[2:]
		embedding_array = np.array(vals, dtype=float)
		size = len(vals)

		# state embeddings for a word = the MAIN embedding for that word *plus* the state-specific deviation
		# "wicked" in MA = wicked/MAIN + wicked/MA

		if facet == "MAIN":
			for n in embeddings:
				if word not in embeddings[n]:
					embeddings[n][word] = np.zeros(size)
				# end if
			# end for
				embeddings[n][word] += embedding_array
		else:
			if word not in embeddings[facet]:
				embeddings[facet][word] = np.zeros(size)
			# end if
			embeddings[facet][word] += embedding_array
		# end if
	# end for

	file.close()

	normalize(embeddings)
	return embeddings

# end def


def compute_pairwise_similarity_multiprocess(embeddings, words, per_country_dist, norm_dist, l1_1, l1_2):

	processes = []
	output = mp.Queue()
	words_per_process = int(len(words)/4)+1

	for p in range(4): # four processes (as the # of CPUs)
		current_words = words[p*words_per_process : (p+1)*words_per_process]
		processes.append(mp.Process(target=compute_pairwise_euclidean_embed_similarity,
				args=(embeddings, current_words, per_country_dist, norm_dist, l1_1, l1_2, output)))
	# end for

	scores = []
	# run processes
	for p in processes:	p.start()
	# get finished process results from the output queue
	for p in processes: scores.extend(output.get())
	# exit the completed processes
	for p in processes:	p.join()

	return np.mean(scores)

# end def


def compute_pairwise_euclidean_embed_similarity(embeddings, words, country_dist, norm_frequency, l1_1, l1_2, output):
	freq_l1_1 = country_dist[l1_1]
	freq_l1_2 = country_dist[l1_2]
	embeddings_l1_1 = embeddings[l1_1]
	embeddings_l1_2 = embeddings[l1_2]

	scores = []
	for word in words:
		try:
			# embedding vectors are unit-normalized
			word_freq_l1_1 = freq_l1_1.get(word, 0)
			word_freq_l1_2 = freq_l1_2.get(word, 0)

			a = np.ones(1) * word_freq_l1_1
			b = np.ones(1) * word_freq_l1_2
			dist = cityblock(a, b) # manhattan distance for vectors
			if word not in embeddings_l1_1.keys() or word not in embeddings_l1_2.keys():
				#print(word, 'not found in embeddings of', l1_1, l1_2)
				continue
			# end if

			wf = norm_frequency[word]  # word frequency in collection
			cosine = np.inner(embeddings_l1_1[word], embeddings_l1_2[word])
			if cosine == 1.0 or dist == 0.0: scores.append(0.0)  # due to math.pow() exception
			else: scores.append(math.pow((1.0-cosine), wf) * math.pow(dist, (1-wf)))
			#else: scores.append(math.pow((1.0-cosine), 0.0) * math.pow(dist, 1.0))

		except ValueError as exception:
			#print(word, l1_1, l1_2, cosine, dist, exception)
			continue
		# end try
	# end for

	output.put(scores)
# end def


def load_word_counts(vocab_filename):
	freq_dist = dict()
	with open(vocab_filename, 'r') as fin:
		for line in fin:
			freq_dist[line.strip().split()[1]] = int(line.strip().split()[0])
		# end for
	# end with
	return freq_dist
# end def


FOCUSED_VOCABULARY = 'focused.dat'
VOCAB_FREQUENCY_FILENAME = 'vocab.countries.pkl'
FULL_VOCABULARY_FILENAME = 'vocabulary.100.dat'

if __name__ == "__main__":

	country_dist = load_obj(VOCAB_FREQUENCY_FILENAME)
	freq_dist = load_word_counts(FULL_VOCABULARY_FILENAME)
	norm_dist = normalize_dist(freq_dist)

	with open(FOCUSED_VOCABULARY) as fin: words = [word.strip() for word in fin]
	with open('countries.dat') as fin: countries = [country.strip() for country in fin]

	emb_filename = 'out.embeddings'
	embeddings = parse_embeddings(emb_filename)

	#print('loaded data, computing similarities...')
	for l1 in itertools.product(countries, countries):
		sim = compute_pairwise_similarity_multiprocess(embeddings, words, country_dist, norm_dist, l1[0], l1[1])

		print(l1[0], l1[1], 'distance:', sim)
		sys.stdout.flush()
	# end for


# end if
