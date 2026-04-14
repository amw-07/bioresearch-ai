'use client';
import { useState } from 'react';
 import Link from'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { SemanticSearchBar } from '@/components/charts/SemanticSearchBar';
import { GuestBanner } from '@/components/ui/GuestBanner';
import { researchersService, SemanticSearchResult, SearchQuota } from '@/lib/api/researchers-service';
import { Researcher } from '@/types/researcher';
import { Eye } from 'lucide-react';

const AREA_LABELS: Record<string, string> = {
  toxicology: 'Toxicology', drug_safety: 'Drug Safety', drug_discovery: 'Drug Discovery',
  organoids: 'Organoids', in_vitro: 'In Vitro', biomarkers: 'Biomarkers',
  preclinical: 'Preclinical', general_biotech: 'General Biotech',
}

const TIER_VARIANT: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  HIGH: 'default', MEDIUM: 'secondary', LOW: 'outline', UNSCORED: 'outline',
}

function pct(n: number | null | undefined) {
  if (n == null) return '—'
  return `${Math.round(n * 100)}%`
}

function ResearcherRow({ r }: { r: Researcher }) {
  return (
    <div className="flex items-start justify-between gap-4 rounded-lg border border-border bg-card p-4 transition-colors hover:bg-accent/30">
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2 mb-1">
          <span className="font-semibold text-sm">{r.name}</span>
          {r.relevance_tier && r.relevance_tier !== 'UNSCORED' && (
            <Badge variant={TIER_VARIANT[r.relevance_tier]} className="text-[10px]">
              {r.relevance_tier.charAt(0) + r.relevance_tier.slice(1).toLowerCase()}
            </Badge>
          )}
          {r.research_area && <Badge variant="outline" className="text-[10px]">{AREA_LABELS[r.research_area] ?? r.research_area}</Badge>}
        </div>
        {r.title && <p className="text-xs text-muted-foreground truncate">{r.title}</p>}
        {r.company && <p className="text-xs text-muted-foreground">{r.company}</p>}
        <div className="mt-2 flex flex-wrap gap-3 text-[11px] text-muted-foreground">
          {r.relevance_score != null && <span>Relevance: <strong className="text-foreground">{r.relevance_score}</strong></span>}
          {r.semantic_similarity != null && <span>Semantic Match: <strong className="text-[#00d68f]">{pct(r.semantic_similarity)}</strong></span>}
          {r.hybrid_score != null && <span>Hybrid Score: <strong className="text-foreground">{pct(r.hybrid_score)}</strong></span>}
          {r.publication_count > 0 && <span>Publications: <strong className="text-foreground">{r.publication_count}</strong></span>}
        </div>
        {r.intelligence?.key_topics && r.intelligence.key_topics.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {r.intelligence.key_topics.slice(0, 4).map((t) => (
              <span key={t} className="rounded px-1.5 py-0.5 text-[10px] bg-[rgba(0,214,143,0.1)] text-[#00d68f] border border-[rgba(0,214,143,0.2)]">{t}</span>
            ))}
          </div>
        )}
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <Link href={`/dashboard/researchers/${r.id}`} className="flex items-center gap-1 rounded-md border border-border px-2 py-1.5 text-xs text-muted-foreground hover:text-foreground hover:bg-accent transition-colors">
          <Eye className="h-3 w-3" />View
        </Link>
      </div>
    </div>
  )
}

export default function SearchPage() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<SemanticSearchResult | null>(null)
  const [quota, setQuota] = useState<SearchQuota | null>(null)

  const runSearch = async (query: string, researchArea: string) => {
    setLoading(true)
    try {
      const payload = await researchersService.semanticSearch({
        query,
        research_area: researchArea === 'all' ? undefined : researchArea,
        n_results: 50,
      })
      setResult(payload)
      if (payload.quota) setQuota(payload.quota)
    } catch (err: any) {
      if (err?.response?.status === 429) {
        const detail = err.response.data?.detail
        if (detail?.searches_limit != null) {
          setQuota({ is_guest: detail.is_guest ?? true, searches_used: detail.searches_limit, searches_limit: detail.searches_limit })
        }
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Search</h1>
        <p className="text-muted-foreground">Semantic search across indexed researchers.</p>
      </div>
      {quota && <GuestBanner searchesUsed={quota.searches_used} searchesLimit={quota.searches_limit} isGuest={quota.is_guest} />}
      <SemanticSearchBar loading={loading} onSearch={runSearch} />
      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-baseline gap-2">
              Results for &quot;{result.query}&quot;
              <span className="text-sm font-normal text-muted-foreground">{result.results_count} found</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {result.researchers.length === 0 ? (
              <p className="text-sm text-muted-foreground">{result.message || 'No matches found. Try a different query or seed more researchers first.'}</p>
            ) : (
              <div className="space-y-3">
                {result.researchers.map((r) => <ResearcherRow key={r.id} r={r} />)}
              </div>
            )}
          </CardContent>
        </Card>
      )}
      {!result && !loading && (
        <div className="rounded-xl border border-dashed border-border p-12 text-center text-muted-foreground">
          <p className="text-sm">Enter a query above to search across indexed researchers.</p>
          <p className="mt-1 text-xs opacity-60">Try: &quot;liver toxicity organoids&quot; · &quot;preclinical drug safety&quot; · &quot;organ-on-chip microphysiological&quot;</p>
        </div>
      )}
    </div>
  )
}
