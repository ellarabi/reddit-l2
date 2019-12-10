import codecs
from nltk.corpus import wordnet as wn
import pickle


def read_vocabulary(filename):
	vocabulary = {}
	with codecs.open(filename, 'r', 'utf-8') as fvoc:
		for line in fvoc:
			vocabulary[line.strip().lower().split()[0]] = None
		# end for
	# end with
	return vocabulary
# end def


def upload_etymological_dataset(filename):
	etymology = {}
	with codecs.open(filename, 'r', 'utf-8') as fet:
		for line in fet:
			entry = line.strip().lower()
			origin = entry.split('\t')[0]
			etymology[origin] = entry.split('\t')[2]
		# end for
	# end with
	return etymology
# end def


def extract_words_roots(etymology):
	roots = {}
	for token in etymology.keys():
		# e.g., token == 'eng: world', 'lat: sun'
		if not token.startswith('eng:'): continue
		original = token.split()[1]

		root_languages = []
		processed_tokens = []
		while token in etymology.keys():
			processed_tokens.append(token)
			if etymology[token] in processed_tokens: break # enm: povre rel:etymology enm: povre
			root_languages.append(etymology[token].split()[0][:-1])
			token = etymology[token]
		# end while

		if len(root_languages) == 0: continue # ignore words with empty roots
		roots[original] = list(set(root_languages))
	# end for
	return roots
# end def


def get_prevalent_pos(token):
	adj =  vocab_pos['A'].get(token, 0)
	noun = vocab_pos['N'].get(token, 0)
	verb = vocab_pos['V'].get(token, 0)

	max = adj; label = 'a'
	if noun > max: max = noun; label = 'n'
	if verb > max: max = verb; label = 'v'

	return label
# end def


def generate_synsets(etymology, vocab, roots):
	synsets = []
	for key in etymology.keys():
		token = key.split()[1] # e.g., eng: attract
		if token not in vocab.keys(): continue
		postag = get_prevalent_pos(token)

		try:
			token_synset = wn.synset(token + '.' + postag + '.01')
		except:
			# it's not an English word according to wordnet
			#print('exception retrieving wordnet synsets for', token, postag)
			continue
		# end try

		if len(token_synset.lemmas()) == 1: continue # single word, no synonyms

		synset = []
		for lemma in token_synset.lemmas():
			if not str(lemma.name()).isalpha() or str(lemma.name()) not in vocab.keys(): continue
			if lemma.name().lower() not in roots.keys():
				continue
			# end if

			synset.append(str(lemma.name()).lower())
		# end for
		if len(synset) < 2: continue # it's a single word eventually
		synsets.append(synset)
	# end for
	return synsets
# end def


def filter_out_etymologically_homogeneous_synsets(synsets, roots):
	heterogeneous_synsets = []
	for synset in synsets:
		fullroots = []
		for word in synset:
			fullroots.extend(roots[word])
		# end for

		if set(fullroots) == set(roots[synset[0]]):
			#print('fitered out', synset, set(fullroots))
			continue
		# end if
		heterogeneous_synsets.append(synset)
	# end for
	return heterogeneous_synsets
# end def


def filter_out_country_specific_lexicon(synsets, filename):
	with codecs.open(filename, 'r', 'utf-8') as fin:
		lexicon = [word.strip() for word in fin]
	# end with

	seed_synsets = []
	for synset in synsets:
		filtered = [word for word in synset if word not in lexicon]
		if len(filtered) < 2:
			#print('filtered out', synset)
			continue
		# end if
		seed_synsets.append(filtered)
	# end for

	return seed_synsets
# end def


def filter_out_synsets_with_prevalent_words(synsets, filename):
	dist_dict = {}
	with open(filename, 'r') as fin:
		for line in fin:
			dist_dict[line.strip().split()[0]] = line.strip().split()[1]
		# end for
	# end with

	seed_synsets = []
	for synset in synsets:
		counts = [int(dist_dict[word]) for word in synset if word in dist_dict.keys()]
		if len(counts) != len(synset):
			print('token(s) not found in dictionary', synset)
			continue
		# end if

		include = True
		normalized_counts = [float(count)/sum(counts) for count in counts]
		for norm_count in normalized_counts:
			if norm_count > PROB_THRESHOLD: include = False
		# end for
		if not include: continue

		seed_synsets.append(synset)
	# end for

	return seed_synsets
# end def


def print_synsets(filename, synsets):
	with codecs.open(filename, 'w', 'utf-8') as fout:
		for synset in synsets:
			fout.write(' '.join(synset) + '\n')
		# end for
	# end with
# end def


def exist_in_wordnet(etymology):
	count = 0
	for token in etymology.keys():
		if not token.startswith('eng:'): continue
		word = token.split()[1].strip()

		if len(wn.synsets(word)) == 0: continue
		count += 1
	# end for
	return count
# end def


PROB_THRESHOLD = 0.9
SIGNIFICANCE_RATE = str(5)

with open('vocab.pos.pkl', 'rb') as fin: vocab_pos = pickle.load(fin)

print('uploading the etymology dataset...')
etymology = upload_etymological_dataset('etymwn.etymology.rel.tsv')
print('constructed etymology dictionary with', len(etymology.keys()), 'entries')

roots = extract_words_roots(etymology)

print('reading dataset filtered vocabulary file...')
vocab_filename = 'vocab.no.entities.pos.100.dat'
vocabulary = read_vocabulary(vocab_filename)
print('total words in vocabulary:', len(vocabulary.keys()))

synsets = generate_synsets(etymology, vocabulary, roots)
print('generated', len(synsets), 'synsets with multiple words')
print_synsets('synsets.mult.initial.100.dat', synsets)

print('filtering out synsets with country specific lexicon...')
SIGNIFICANT_WORDS = 'significant.words.' + SIGNIFICANCE_RATE + '.dat'
synsets = filter_out_country_specific_lexicon(synsets, SIGNIFICANT_WORDS)
print_synsets('synsets.mult.without.country.lex.100.dat', synsets)

print('filtering out synsets with extremely prevalent word(s)...')
synsets = filter_out_synsets_with_prevalent_words(synsets, vocab_filename)
print_synsets('synsets.mult.without.prev.100.dat', synsets)

print('filtering out etymologically homogeneous sysnets...')
synsets = filter_out_etymologically_homogeneous_synsets(synsets, roots)
print_synsets('synsets.mult.final.100.dat', synsets)


words = list()
for synset in synsets: words.extend(synset)

with codecs.open('focused.set.' + SIGNIFICANCE_RATE + '.' + str(PROB_THRESHOLD) + '.dat', 'w', 'utf-8') as fout:
	fout.write('\n'.join(list(set(words))) + '\n')
# end with

print('finished')
