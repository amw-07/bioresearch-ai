'use client';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export interface SHAPContribution {
  feature: string
  display_name: string
  shap_value: number
  direction: 'positive' | 'negative'
}

interface ScoreExplanationCardProps {
  relevance_score: number | null
  relevance_tier: string | null
  research_area?: string | null
  shap_contributions: SHAPContribution[] | null | undefined
}

const TIER_COLORS: Record<string, string> = {
  HIGH: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
  MEDIUM: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  LOW: 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30',
  UNSCORED: 'bg-zinc-700/20 text-zinc-500 border-zinc-600/30',
}

const POSITIVE_COLOR = '#00d68f'
const NEGATIVE_COLOR = '#f87171'

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload
    return (
      <div className="rounded-md border border-white/10 bg-[hsl(220,45%,8%)] px-3 py-2 text-xs shadow-lg">
        <p className="font-medium text-zinc-200">{data.display_name}</p>
        <p style={{ color: data.direction === 'positive' ? POSITIVE_COLOR : NEGATIVE_COLOR }}>
          SHAP: {data.shap_value > 0 ? '+' : ''}
          {data.shap_value.toFixed(4)}
        </p>
        <p className="capitalize text-zinc-500">{data.direction} contribution</p>
      </div>
    )
  }

  return null
}

export function ScoreExplanationCard({
  relevance_score,
  relevance_tier,
  research_area,
  shap_contributions,
}: ScoreExplanationCardProps) {
  const tier = relevance_tier ?? 'UNSCORED'
  const tierClass = TIER_COLORS[tier] ?? TIER_COLORS.UNSCORED

  const chartData = (shap_contributions ?? [])
    .map((contribution) => ({
      display_name: contribution.display_name,
      shap_value: contribution.shap_value,
      abs_value: Math.abs(contribution.shap_value),
      direction: contribution.direction,
    }))
    .sort((a, b) => b.abs_value - a.abs_value)
    .slice(0, 5)

  const hasData = chartData.length > 0

  return (
    <Card className="border-white/[0.06] bg-[hsl(220,45%,6%)]">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <CardTitle className="font-syne text-base font-semibold text-zinc-100">
            Score Explanation
          </CardTitle>
          <div className="flex flex-wrap items-center justify-end gap-2">
            <span className="font-syne text-2xl font-bold tabular-nums text-white">
              {relevance_score ?? '—'}
            </span>
            <Badge variant="outline" className={`px-2 py-0.5 font-mono text-xs border ${tierClass}`}>
              {tier}
            </Badge>
            {research_area && (
              <Badge
                variant="outline"
                className="border-[rgba(0,214,143,0.25)] bg-[rgba(0,214,143,0.08)] px-2 py-0.5 text-xs text-[#00d68f]"
              >
                {research_area}
              </Badge>
            )}
          </div>
        </div>
        <p className="mt-1 text-xs text-zinc-500">
          Top 5 feature contributions via SHAP TreeExplainer
        </p>
      </CardHeader>

      <CardContent>
        {!hasData ? (
          <div className="flex h-32 items-center justify-center rounded-md border border-dashed border-white/10">
            <p className="text-xs text-zinc-600">
              Score explanation unavailable — run enrichment to generate SHAP values
            </p>
          </div>
        ) : (
          <>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ top: 4, right: 16, bottom: 4, left: 8 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="rgba(255,255,255,0.04)"
                  horizontal={false}
                />
                <XAxis
                  type="number"
                  tick={{ fontSize: 10, fill: '#52525b' }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => value.toFixed(2)}
                />
                <YAxis
                  type="category"
                  dataKey="display_name"
                  tick={{ fontSize: 10, fill: '#a1a1aa' }}
                  tickLine={false}
                  axisLine={false}
                  width={140}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                <Bar dataKey="shap_value" radius={[0, 3, 3, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.direction === 'positive' ? POSITIVE_COLOR : NEGATIVE_COLOR}
                      fillOpacity={0.85}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>

            <div className="mt-3 flex justify-center gap-4">
              <div className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: POSITIVE_COLOR }} />
                <span className="text-[10px] text-zinc-500">Positive contribution</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: NEGATIVE_COLOR }} />
                <span className="text-[10px] text-zinc-500">Negative contribution</span>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
