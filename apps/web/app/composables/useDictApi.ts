import type { EntryDetail, ParseResponse, SearchResponse } from '@germandict/shared-types'
import { useRuntimeConfig } from '#app'

export interface DictApi {
  search: (query: string, limit?: number) => Promise<SearchResponse>
  getEntry: (lexemeId: string) => Promise<EntryDetail>
  parse: (text: string) => Promise<ParseResponse>
}

export function useDictApi(): DictApi {
  const config = useRuntimeConfig()
  const base = String(config.public.apiBase).replace(/\/+$/, '')

  return {
    search(query: string, limit = 25) {
      return $fetch<SearchResponse>(`${base}/api/search`, {
        params: { q: query, limit },
      })
    },
    getEntry(lexemeId: string) {
      return $fetch<EntryDetail>(`${base}/api/entries/${encodeURIComponent(lexemeId)}`)
    },
    parse(text: string) {
      return $fetch<ParseResponse>(`${base}/api/parse`, { params: { text } })
    },
  }
}
