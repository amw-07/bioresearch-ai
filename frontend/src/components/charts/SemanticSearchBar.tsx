'use client';

import { useState, useRef, useEffect } from 'react';
import { Search, Zap, ChevronRight } from 'lucide-react';

const FILTERS = [
  { value: 'all', label: 'All Domains' },
  { value: 'toxicology', label: 'Toxicology' },
  { value: 'drug_safety', label: 'Drug Safety' },
  { value: 'dili_hepatotoxicity', label: 'DILI' },
  { value: 'drug_discovery', label: 'Drug Discovery' },
  { value: 'organoids_3d_models', label: 'Organoids' },
  { value: 'in_vitro_models', label: 'In Vitro' },
  { value: 'preclinical', label: 'Preclinical' },
  { value: 'biomarkers', label: 'Biomarkers' },
];

const EXAMPLE_QUERIES = [
  'organ-on-chip hepatotoxicity assay',
  'preclinical drug safety ADME',
  'DILI biomarker clinical translation',
  'liver organoid toxicity screening',
];

interface Props {
  loading?: boolean;
  onSearch: (query: string, researchArea: string) => void;
}

export function SemanticSearchBar({ loading = false, onSearch }: Props) {
  const [query, setQuery] = useState('');
  const [researchArea, setResearchArea] = useState('all');
  const [focused, setFocused] = useState(false);
  const [scanLine, setScanLine] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  // Animate the scanner line on the search button when loading
  useEffect(() => {
    if (!loading) { setScanLine(0); return; }
    const id = setInterval(() => setScanLine((p) => (p + 1) % 100), 20);
    return () => clearInterval(id);
  }, [loading]);

  const submit = () => {
    const trimmed = query.trim();
    if (!trimmed || loading) return;
    onSearch(trimmed, researchArea);
  };

  const fillExample = (ex: string) => {
    setQuery(ex);
    inputRef.current?.focus();
  };

  return (
    <div className="w-full space-y-4">

      {/* ── Header label ─────────────────────────────────────────── */}
      <div className="flex items-center gap-2.5">
        <div
          className="flex h-6 w-6 items-center justify-center rounded"
          style={{
            background: 'rgba(0,214,143,0.12)',
            border: '1px solid rgba(0,214,143,0.25)',
          }}
        >
          <Zap className="h-3 w-3" style={{ color: '#00d68f' }} />
        </div>
        <span
          className="font-mono-dm text-[11px] uppercase tracking-[0.18em]"
          style={{ color: '#00d68f' }}
        >
          Semantic Search
        </span>
        <div
          className="ml-auto rounded-full px-2 py-0.5 font-mono-dm text-[10px] tracking-widest"
          style={{
            color: 'rgba(0,214,143,0.55)',
            border: '1px solid rgba(0,214,143,0.15)',
            background: 'rgba(0,214,143,0.04)',
          }}
        >
          sentence-transformers · all-MiniLM-L6-v2
        </div>
      </div>

      {/* ── Main search input ────────────────────────────────────── */}
      <div
        className="relative overflow-hidden transition-all duration-200"
        style={{
          borderRadius: '10px',
          border: focused
            ? '1px solid rgba(0,214,143,0.45)'
            : '1px solid rgba(255,255,255,0.07)',
          background: 'rgba(10,16,32,0.85)',
          backdropFilter: 'blur(16px)',
          boxShadow: focused
            ? '0 0 0 3px rgba(0,214,143,0.08), 0 4px 24px rgba(0,0,0,0.4)'
            : '0 2px 12px rgba(0,0,0,0.3)',
        }}
      >
        {/* scanning glow line at top when focused */}
        {focused && (
          <div
            className="pointer-events-none absolute left-0 right-0 top-0 h-px"
            style={{
              background:
                'linear-gradient(90deg, transparent 0%, rgba(0,214,143,0.6) 50%, transparent 100%)',
            }}
          />
        )}

        <div className="flex items-center gap-0">
          {/* Search icon */}
          <div className="flex items-center pl-4">
            <Search
              className="h-4 w-4 transition-colors"
              style={{ color: focused ? '#00d68f' : 'rgba(255,255,255,0.25)' }}
            />
          </div>

          {/* Input */}
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && submit()}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            placeholder="e.g. organ-on-chip hepatotoxicity assay"
            disabled={loading}
            className="flex-1 bg-transparent py-3.5 pl-3 pr-2 text-sm text-white outline-none placeholder:text-zinc-600"
            style={{ fontFamily: 'DM Sans, sans-serif' }}
          />

          {/* Kbd hint */}
          <div className="hidden items-center gap-1 pr-3 sm:flex">
            <kbd
              className="rounded px-1.5 py-0.5 font-mono-dm text-[10px]"
              style={{
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                color: 'rgba(255,255,255,0.3)',
              }}
            >
              ↵
            </kbd>
          </div>

          {/* Search button */}
          <button
            onClick={submit}
            disabled={loading || !query.trim()}
            className="relative m-1.5 flex items-center gap-2 overflow-hidden rounded-md px-4 py-2 text-sm font-medium transition-all duration-150"
            style={{
              background:
                loading || !query.trim()
                  ? 'rgba(0,214,143,0.08)'
                  : 'rgba(0,214,143,0.15)',
              border:
                loading || !query.trim()
                  ? '1px solid rgba(0,214,143,0.12)'
                  : '1px solid rgba(0,214,143,0.35)',
              color:
                loading || !query.trim()
                  ? 'rgba(0,214,143,0.35)'
                  : '#00d68f',
              cursor: loading || !query.trim() ? 'not-allowed' : 'pointer',
            }}
          >
            {/* loading scanner overlay */}
            {loading && (
              <div
                className="pointer-events-none absolute inset-0"
                style={{
                  background: `linear-gradient(90deg, transparent ${scanLine - 20}%, rgba(0,214,143,0.2) ${scanLine}%, transparent ${scanLine + 20}%)`,
                }}
              />
            )}
            {loading ? (
              <>
                <span
                  className="h-3 w-3 animate-spin rounded-full border border-current border-t-transparent"
                />
                <span className="font-mono-dm text-xs tracking-widest">
                  SCANNING
                </span>
              </>
            ) : (
              <>
                <ChevronRight className="h-3.5 w-3.5" />
                <span className="font-mono-dm text-xs tracking-widest">
                  SEARCH
                </span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* ── Sub-label ─────────────────────────────────────────────── */}
      <p
        className="font-mono-dm text-[11px]"
        style={{ color: 'rgba(255,255,255,0.22)', letterSpacing: '0.04em' }}
      >
        Semantic search across biotech research · powered by sentence-transformers
      </p>

      {/* ── Domain filter pills ───────────────────────────────────── */}
      <div className="flex flex-wrap gap-1.5">
        {FILTERS.map((filter) => {
          const active = researchArea === filter.value;
          return (
            <button
              key={filter.value}
              onClick={() => setResearchArea(filter.value)}
              className="rounded-full px-3 py-1 font-mono-dm text-[11px] tracking-wide transition-all duration-150"
              style={{
                background: active
                  ? 'rgba(0,214,143,0.14)'
                  : 'rgba(255,255,255,0.04)',
                border: active
                  ? '1px solid rgba(0,214,143,0.4)'
                  : '1px solid rgba(255,255,255,0.08)',
                color: active ? '#00d68f' : 'rgba(255,255,255,0.38)',
                boxShadow: active ? '0 0 10px rgba(0,214,143,0.12)' : 'none',
                cursor: 'pointer',
              }}
            >
              {filter.label}
            </button>
          );
        })}
      </div>

      {/* ── Example queries ───────────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
        <span
          className="font-mono-dm text-[10px] uppercase tracking-widest"
          style={{ color: 'rgba(255,255,255,0.2)' }}
        >
          Try:
        </span>
        {EXAMPLE_QUERIES.map((ex) => (
          <button
            key={ex}
            onClick={() => fillExample(ex)}
            className="rounded font-mono-dm text-[11px] transition-colors duration-100"
            style={{ color: 'rgba(255,255,255,0.3)' }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.color = 'rgba(0,214,143,0.7)')
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.color = 'rgba(255,255,255,0.3)')
            }
          >
            {ex}
          </button>
        ))}
      </div>
    </div>
  );
}