import type { GrammaticalFeatures, MatchType } from '@germandict/shared-types'

export interface HighlightSegment {
  text: string
  mark: boolean
}

const POS_LABELS: Record<string, string> = {
  noun: 'Nomen',
  proper_noun: 'Eigenname',
  verb: 'Verb',
  auxiliary: 'Hilfsverb',
  adjective: 'Adjektiv',
  adverb: 'Adverb',
  pronoun: 'Pronomen',
  determiner: 'Artikelwort',
  preposition: 'Präposition',
  conjunction: 'Konjunktion',
  numeral: 'Numerale',
  particle: 'Partikel',
  interjection: 'Interjektion',
  other: 'Andere',
}

const MATCH_LABELS: Record<MatchType, string> = {
  lemma: 'Lemma',
  form: 'Beugte Form',
  normalized: 'Schreibvariante',
  morphology: 'Morphologie',
  definition: 'in Definition gefunden',
  fuzzy: 'Tippfehler-Korrektur',
}

const FORM_TYPE_LABELS: Record<string, string> = {
  lemma: 'Grundform',
  inflected: 'flektierte Form',
  declined: 'deklinierte Form',
  comparative: 'Komparativ',
  superlative: 'Superlativ',
  participle: 'Partizip',
  present: 'Präsens',
  past: 'Präteritum',
  plural: 'Plural',
}

const CASE_LABELS: Record<string, string> = {
  Nom: 'Nominativ',
  Akk: 'Akkusativ',
  Dat: 'Dativ',
  Gen: 'Genitiv',
}

const NUMBER_LABELS: Record<string, string> = {
  Sing: 'Singular',
  Plur: 'Plural',
}

const GENDER_LABELS: Record<string, string> = {
  masc: 'maskulin',
  fem: 'feminin',
  neut: 'neutrum',
}

const TENSE_LABELS: Record<string, string> = {
  Pres: 'Präsens',
  Perf: 'Perfekt',
  Past: 'Präteritum',
  Plus: 'Plusquamperfekt',
  Fut: 'Futur',
}

const MOOD_LABELS: Record<string, string> = {
  Ind: 'Indikativ',
  Konj1: 'Konjunktiv I',
  Konj2: 'Konjunktiv II',
  Imp: 'Imperativ',
}

const VERB_FORM_LABELS: Record<string, string> = {
  Fin: 'finite Form',
  Part: 'Partizip II',
  Inf: 'Infinitiv',
}

const DEGREE_LABELS: Record<string, string> = {
  Pos: 'positiv',
  Cmp: 'Komparativ',
  Sup: 'Superlativ',
}

const VOICE_LABELS: Record<string, string> = {
  Act: 'Aktiv',
  Pass: 'Passiv',
}

const RELATION_LABELS: Record<string, string> = {
  synonym: 'Synonym',
  antonym: 'Gegenteil',
  hyponym: 'Unterbegriff',
  hyperonym: 'Oberbegriff',
}

const REGISTER_LABELS: Record<string, string> = {
  colloquial: 'umgangssprachlich',
  formal: 'schriftsprachlich',
  archaic: 'veraltet',
  regional: 'regional',
}

const ARTICLE_BY_GENDER: Record<string, string> = {
  masc: 'der',
  fem: 'die',
  neut: 'das',
  plural: 'die',
}

export function posLabel(partOfSpeech: string): string {
  return POS_LABELS[partOfSpeech] ?? partOfSpeech
}

export function matchTypeLabel(matchType: MatchType): string {
  return MATCH_LABELS[matchType] ?? matchType
}

export function formTypeLabel(formType: string): string {
  return FORM_TYPE_LABELS[formType] ?? formType
}

export function relationTypeLabel(relationType: string): string {
  return RELATION_LABELS[relationType] ?? relationType
}

export function registerLabel(register: string): string {
  return REGISTER_LABELS[register] ?? register
}

export function articleForGender(gender: string | null | undefined): string | null {
  if (!gender) return null
  return ARTICLE_BY_GENDER[gender] ?? null
}

export function frequencyLabel(rank: number | null | undefined): string | null {
  if (rank === null || rank === undefined) return null
  return `Häufigkeit #${rank.toLocaleString('de-DE')}`
}

export function principalFormsLabel(forms: string[]): string {
  return forms.join(' · ')
}

function tokens(
  value: string | null | undefined,
  labels: Record<string, string> | null = null,
): string[] {
  if (!value) return []
  if (!labels) return [value]
  return [labels[value] ?? value]
}

export function formatFeatures(features: GrammaticalFeatures | null | undefined): string[] {
  if (!features) return []
  const result: string[] = []
  if (features.case) result.push(...tokens(features.case, CASE_LABELS))
  if (features.number) result.push(...tokens(features.number, NUMBER_LABELS))
  if (features.gender) result.push(...tokens(features.gender, GENDER_LABELS))
  if (features.tense) result.push(...tokens(features.tense, TENSE_LABELS))
  if (features.mood) result.push(...tokens(features.mood, MOOD_LABELS))
  if (features.person) result.push(`${features.person}. Person`)
  if (features.verb_form) result.push(...tokens(features.verb_form, VERB_FORM_LABELS))
  if (features.degree) result.push(...tokens(features.degree, DEGREE_LABELS))
  if (features.voice) result.push(...tokens(features.voice, VOICE_LABELS))
  if (features.extra) {
    for (const [key, value] of Object.entries(features.extra)) {
      result.push(`${key}: ${value}`)
    }
  }
  return result
}

export interface Highlight {
  startOffset: number
  endOffset: number
}

export function sliceHighlighted(text: string, highlights: Highlight[]): HighlightSegment[] {
  const segments: HighlightSegment[] = []
  const ordered = [...highlights]
    .filter((h) => h.startOffset >= 0 && h.endOffset > h.startOffset && h.endOffset <= text.length)
    .sort((a, b) => a.startOffset - b.startOffset)

  let cursor = 0
  for (const highlight of ordered) {
    if (highlight.startOffset < cursor) continue
    if (highlight.startOffset > cursor) {
      segments.push({ text: text.slice(cursor, highlight.startOffset), mark: false })
    }
    segments.push({ text: text.slice(highlight.startOffset, highlight.endOffset), mark: true })
    cursor = highlight.endOffset
  }
  if (cursor < text.length) {
    segments.push({ text: text.slice(cursor), mark: false })
  }
  if (segments.length === 0 && text.length > 0) {
    segments.push({ text, mark: false })
  }
  return segments
}
