import lru
import nltk

from textattack.constraints import Constraint
from textattack.shared import TokenizedText
from textattack.shared.validators import is_word_swap

class PartOfSpeech(Constraint):
    """ Constraints word swaps to only swap words with the same part of speech.
        Uses the NLTK universal part-of-speech tagger by default.
        An implementation of `<https://arxiv.org/abs/1907.11932>`_
        adapted from `<https://github.com/jind11/TextFooler>`_. 
    """
    def __init__(self, tagset='universal', allow_verb_noun_swap=True):
        self.tagset = tagset
        self.allow_verb_noun_swap = allow_verb_noun_swap
        self._pos_tag_cache = lru.LRU(2**14)
  
    def check_compatibility(self, transformation):
        return transformation.consists_of(is_word_swap)

    def _can_replace_pos(self, pos_a, pos_b):
        return (pos_a == pos_b) or (self.allow_verb_noun_swap and set([pos_a,pos_b]) <= set(['NOUN','VERB']))

    def _get_pos(self, before_ctx, word, after_ctx):
        context_words = before_ctx + [word] + after_ctx
        context_key = ' '.join(context_words)
        if context_key in self._pos_tag_cache:
            pos_list = self._pos_tag_cache[context_key]
        else:
            _, pos_list = zip(*nltk.pos_tag(context_words, tagset=self.tagset))
            self._pos_tag_cache[context_key] = pos_list
        return pos_list 
        
    def _check_constraint(self, x, x_adv, original_text=None):
        if not isinstance(x, TokenizedText):
            raise TypeError('x must be of type TokenizedText')
        if not isinstance(x_adv, TokenizedText):
            raise TypeError('x_adv must be of type TokenizedText')
        
        try:
            indices = x_adv.attack_attrs['newly_modified_indices']
        except KeyError:
            raise KeyError('Cannot apply part-of-speech constraint without `newly_modified_indices`')
        
        for i in indices:
            x_word = x.words[i]
            x_adv_word = x_adv.words[i]
            before_ctx = x.words[max(i-4,0):i]
            after_ctx = x.words[i+1:min(i+5,len(x.words))]
            cur_pos = self._get_pos(before_ctx, x_word, after_ctx)
            replace_pos = self._get_pos(before_ctx, x_adv_word, after_ctx)
            if not self._can_replace_pos(cur_pos, replace_pos):
                return False

        return True
    
    def extra_repr_keys(self):
        return ['tagset', 'allow_verb_noun_swap']
