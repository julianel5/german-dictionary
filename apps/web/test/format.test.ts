import type { GrammaticalFeatures } from '@germandict/shared-types'
import { describe, expect, it } from 'vitest'
import {
  articleForGender,
  formatFeatures,
  formTypeLabel,
  frequencyLabel,
  matchTypeLabel,
  posLabel,
  principalFormsLabel,
  relationTypeLabel,
  sliceHighlighted,
} from '~/utils/format'

describe('posLabel', () => {
  it('maps known parts of speech to German labels', () => {
    expect(posLabel('verb')).toBe('Verb')
    expect(posLabel('noun')).toBe('Nomen')
    expect(posLabel('adjective')).toBe('Adjektiv')
  })

  it('falls back to the raw value', () => {
    expect(posLabel('interjection')).toBe('Interjektion')
    expect(posLabel('unknown_pos')).toBe('unknown_pos')
  })
})

describe('matchTypeLabel', () => {
  it('labels every match type', () => {
    expect(matchTypeLabel('lemma')).toBe('Lemma')
    expect(matchTypeLabel('form')).toBe('Beugte Form')
    expect(matchTypeLabel('normalized')).toBe('Schreibvariante')
    expect(matchTypeLabel('morphology')).toBe('Morphologie')
    expect(matchTypeLabel('definition')).toBe('in Definition gefunden')
    expect(matchTypeLabel('fuzzy')).toBe('Tippfehler-Korrektur')
  })
})

describe('formTypeLabel', () => {
  it('maps form types', () => {
    expect(formTypeLabel('lemma')).toBe('Grundform')
    expect(formTypeLabel('participle')).toBe('Partizip')
    expect(formTypeLabel('superlative')).toBe('Superlativ')
    expect(formTypeLabel('mystery')).toBe('mystery')
  })
})

describe('relationTypeLabel', () => {
  it('maps relation types', () => {
    expect(relationTypeLabel('synonym')).toBe('Synonym')
    expect(relationTypeLabel('antonym')).toBe('Gegenteil')
  })
})

describe('articleForGender', () => {
  it('returns the definite article', () => {
    expect(articleForGender('masc')).toBe('der')
    expect(articleForGender('fem')).toBe('die')
    expect(articleForGender('neut')).toBe('das')
    expect(articleForGender(null)).toBeNull()
    expect(articleForGender('unknown')).toBeNull()
  })
})

describe('frequencyLabel', () => {
  it('formats ranks in German locale', () => {
    expect(frequencyLabel(123)).toBe('Häufigkeit #123')
    expect(frequencyLabel(4567)).toBe('Häufigkeit #4.567')
    expect(frequencyLabel(null)).toBeNull()
    expect(frequencyLabel(undefined)).toBeNull()
  })
})

describe('principalFormsLabel', () => {
  it('joins principal forms', () => {
    expect(principalFormsLabel(['gehen', 'ging', 'gegangen'])).toBe('gehen · ging · gegangen')
    expect(principalFormsLabel([])).toBe('')
  })
})

describe('formatFeatures', () => {
  it('returns nothing for missing features', () => {
    expect(formatFeatures(null)).toEqual([])
    expect(formatFeatures(undefined)).toEqual([])
    expect(formatFeatures({})).toEqual([])
  })

  it('translates nominal features', () => {
    const features: GrammaticalFeatures = { case: 'Dat', number: 'Plur', gender: 'neut' }
    expect(formatFeatures(features)).toEqual(['Dativ', 'Plural', 'neutrum'])
  })

  it('translates verbal features', () => {
    const features: GrammaticalFeatures = { tense: 'Past', mood: 'Ind', person: '3' }
    expect(formatFeatures(features)).toEqual(['Präteritum', 'Indikativ', '3. Person'])
    expect(formatFeatures({ verb_form: 'Part' })).toEqual(['Partizip II'])
  })

  it('translates degree and passes through extras', () => {
    expect(formatFeatures({ degree: 'Sup' })).toEqual(['Superlativ'])
    expect(formatFeatures({ extra: { variant: 'ö' } })).toEqual(['variant: ö'])
  })

  it('falls back to the raw value for unknown codes', () => {
    expect(formatFeatures({ case: 'Weird' })).toEqual(['Weird'])
  })
})

describe('sliceHighlighted', () => {
  it('splits text around a highlight', () => {
    const segments = sliceHighlighted('Ich ging nach Hause.', [{ startOffset: 4, endOffset: 8 }])
    expect(segments).toEqual([
      { text: 'Ich ', mark: false },
      { text: 'ging', mark: true },
      { text: ' nach Hause.', mark: false },
    ])
  })

  it('handles multiple highlights in order', () => {
    const segments = sliceHighlighted('Das Haus brennt.', [
      { startOffset: 4, endOffset: 8 },
      { startOffset: 9, endOffset: 15 },
    ])
    expect(segments.map((segment) => segment.mark)).toEqual([false, true, false, true, false])
    expect(segments[1].text).toBe('Haus')
    expect(segments[3].text).toBe('brennt')
    expect(segments[4].text).toBe('.')
  })

  it('returns the plain text when nothing is highlighted', () => {
    expect(sliceHighlighted('Hallo', [])).toEqual([{ text: 'Hallo', mark: false }])
    expect(sliceHighlighted('', [])).toEqual([])
  })

  it('skips out-of-range or inverted highlights', () => {
    const segments = sliceHighlighted('kurz', [
      { startOffset: 3, endOffset: 1 },
      { startOffset: 2, endOffset: 99 },
    ])
    expect(segments).toEqual([{ text: 'kurz', mark: false }])
  })
})
