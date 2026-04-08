import { defineStore } from 'pinia'

export const useLemmaStore = defineStore('lemma-store', {
  state: () => ({
    pos_options: [ 'ADJ', 'ADP', 'ADV', 'AUX',
      'CCONJ', 'DET', 'INTJ', 'NOUN',
      'NUM', 'PART', 'PRON', 'PROPN',
      'PUNCT', 'SCONJ', 'SPACE', 'SYM',
      'VERB', 'X',
    ] as string[],
  }),
})

