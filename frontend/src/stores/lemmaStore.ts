import { defineStore } from 'pinia'

import { patch } from '@/stores/fetchWrapper'
import { on } from '@/socket/socket'
import { SOCKET_EVENT } from '@/socket/events'
import type { LemmaItem } from '@/types/lemmatize'

export const useLemmaStore = defineStore('lemma-store', {
  state: () => ({
    pos_options: [ 'ADJ', 'ADP', 'ADV', 'AUX',
      'CCONJ', 'DET', 'INTJ', 'NOUN',
      'NUM', 'PART', 'PRON', 'PROPN',
      'PUNCT', 'SCONJ', 'SPACE', 'SYM',
      'VERB', 'X',
    ] as string[],
    connected: false as boolean,
  }),
  actions: {
    bindSocketEvents(): void {
      if (this.connected) return
      on(SOCKET_EVENT.LEMMA_EDIT_FAILED, (_socketMsg) => { /* no-op */ })
      this.connected = true
    },

    async editLemmaToken(lemmaId: string, lemmaWord: string, posTag: string): Promise<LemmaItem> {
      return patch<LemmaItem>(`/api/lemma/${lemmaId}`, 
        { lemma_word: lemmaWord, pos_tag: posTag })
    },
  },
})

