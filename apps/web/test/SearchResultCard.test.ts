import type { SearchResultItem } from '@germandict/shared-types'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import SearchResultCard from '~/components/SearchResultCard.vue'

const gingResult: SearchResultItem = {
  lexemeId: 'lexeme:verb:gehen',
  lemma: 'gehen',
  matchedSurface: 'ging',
  matchedFormId: 'form:gehen:past',
  partOfSpeech: 'verb',
  frequencyRank: 123,
  matchType: 'form',
  gender: null,
  definition: 'sich zu Fuß fortbewegen',
  principalForms: ['gehen', 'ging', 'gegangen'],
  analysis: { tense: 'Past', mood: 'Ind', person: '3', number: 'Sing' },
  morphCertainty: 1,
  score: 6345,
}

const NuxtLinkStub = {
  template: '<a :href="to"><slot /></a>',
  props: { to: { type: String, required: true } },
}

function mountCard(result: SearchResultItem) {
  return mount(SearchResultCard, {
    props: { result },
    global: { stubs: { NuxtLink: NuxtLinkStub } },
  })
}

describe('SearchResultCard', () => {
  it('shows lemma, part of speech and frequency', () => {
    const wrapper = mountCard(gingResult)
    const text = wrapper.text()
    expect(text).toContain('gehen')
    expect(text).toContain('Verb')
    expect(text).toContain('Häufigkeit #123')
    expect(text).toContain('gehen · ging · gegangen')
    expect(text).toContain('sich zu Fuß fortbewegen')
  })

  it('labels an inflected match with its surface form', () => {
    const wrapper = mountCard(gingResult)
    const text = wrapper.text()
    expect(text).toContain('Beugte Form')
    expect(text).toContain('ging')
    expect(text).toContain('Präteritum')
    expect(text).toContain('3. Person')
  })

  it('omits the inflected-form label for an exact lemma match', () => {
    const wrapper = mountCard({
      ...gingResult,
      matchedSurface: 'gehen',
      matchedFormId: null,
      matchType: 'lemma',
    })
    const text = wrapper.text()
    expect(text).not.toContain('Beugte Form')
    expect(text).not.toContain('Schreibvariante')
  })

  it('shows the article for noun results', () => {
    const wrapper = mountCard({
      ...gingResult,
      lemma: 'Haus',
      partOfSpeech: 'noun',
      gender: 'neut',
      principalForms: ['Haus', 'Häuser'],
      analysis: { case: 'Nom', number: 'Sing', gender: 'neut' },
    })
    const text = wrapper.text()
    expect(text).toContain('das')
    expect(text).toContain('Nomen')
    expect(text).toContain('Nominativ')
  })

  it('flags fuzzy fallback results', () => {
    const wrapper = mountCard({
      ...gingResult,
      matchType: 'fuzzy',
      matchedSurface: null,
      matchedFormId: null,
      analysis: null,
    })
    const text = wrapper.text()
    expect(text).toContain('Meinten Sie')
    expect(text).toContain('Tippfehler-Korrektur')
  })

  it('marks low-confidence morphology analyses', () => {
    const wrapper = mountCard({ ...gingResult, morphCertainty: 0.4 })
    expect(wrapper.text()).toContain('unsichere Analyse')
  })

  it('links to the entry page', () => {
    const wrapper = mountCard(gingResult)
    expect(wrapper.find('a').attributes('href')).toBe('/entries/lexeme:verb:gehen')
  })
})
