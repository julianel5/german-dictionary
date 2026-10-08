/**
 * Shared API contracts (mirror of apps/api/app/schemas).
 *
 * Type-only package: import with `import type { ... }` so it erases at
 * build time and carries no runtime code.
 */

export type MatchType =
  | 'lemma'
  | 'form'
  | 'normalized'
  | 'morphology'
  | 'definition'
  | 'fuzzy'

export type PartOfSpeech =
  | 'noun'
  | 'proper_noun'
  | 'verb'
  | 'auxiliary'
  | 'adjective'
  | 'adverb'
  | 'pronoun'
  | 'determiner'
  | 'preposition'
  | 'conjunction'
  | 'numeral'
  | 'particle'
  | 'interjection'
  | 'other'

export interface GrammaticalFeatures {
  case?: string | null
  number?: string | null
  gender?: string | null
  person?: string | null
  tense?: string | null
  mood?: string | null
  degree?: string | null
  voice?: string | null
  verb_form?: string | null
  adjective_form?: string | null
  extra?: Record<string, string>
}

export interface SearchResultItem {
  lexemeId: string
  lemma: string
  matchedSurface: string | null
  matchedFormId: string | null
  partOfSpeech: string
  frequencyRank: number | null
  matchType: MatchType
  gender: string | null
  definition: string | null
  principalForms: string[]
  analysis: GrammaticalFeatures | null
  morphCertainty: number | null
  score: number
}

export interface SearchResponse {
  query: string
  queryType: MatchType | null
  results: SearchResultItem[]
  morphologyEngine: string | null
}

export interface Lexeme {
  id: string
  lemma: string
  language: string
  partOfSpeech: string
  gender: string | null
  register: string | null
  domain: string | null
}

export interface Sense {
  id: string
  senseIndex: number
  definition: string
  register: string | null
  domain: string | null
}

export interface WordForm {
  id: string
  surface: string
  normalizedSurface: string
  formType: string
  isSearchable: boolean
  features: GrammaticalFeatures | null
}

export interface ExampleHighlight {
  wordFormId: string | null
  surface: string
  startOffset: number
  endOffset: number
}

export interface ExampleSentence {
  id: string
  text: string
  translation: string | null
  source: string | null
  highlights: ExampleHighlight[]
}

export interface Frequency {
  corpus: string
  rank: number
  count: number
  wordFormId: string | null
}

export interface Relation {
  relationType: string
  lexemeId: string
  lemma: string
}

export interface EntryDetail {
  lexeme: Lexeme
  senses: Sense[]
  forms: WordForm[]
  examples: ExampleSentence[]
  frequency: Frequency[]
  relations: Relation[]
  principalForms: string[]
}

export interface ParseAnalysis {
  lemma: string
  partOfSpeech: string | null
  features: GrammaticalFeatures
  confidence: number
  engine: string
}

export interface ParseToken {
  surface: string
  start: number
  end: number
  analyses: ParseAnalysis[]
}

export interface ParseResponse {
  text: string
  engine: string | null
  tokens: ParseToken[]
}

export interface HealthResponse {
  status: 'ok' | 'degraded'
  version: string
  database: 'ok' | 'error'
  cache: boolean
  morphologyEngine: string | null
}
