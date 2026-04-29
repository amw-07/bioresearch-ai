'use client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ModelMetrics } from '@/lib/api/researchers-service';

interface Props {
  metrics: ModelMetrics | null
  isLoading?: boolean
}

export function ModelMetricsDashboard({ metrics, isLoading = false }: Props) {
  if (isLoading) return <div className="text-sm text-muted-foreground">Loading model metrics…</div>
  if (!metrics) return <div className="text-sm text-muted-foreground">Model metrics unavailable. Train model to generate eval_v1.json.</div>

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader><CardTitle>Model Overview</CardTitle></CardHeader>
        <CardContent className="grid gap-3 text-sm md:grid-cols-3">
          <div>Type: <span className="font-medium">{metrics.model_type}</span></div>
          <div>Last Trained: <span className="font-medium">{new Date(metrics.trained_at).toLocaleDateString()}</span></div>
          <div>Sample Count: <span className="font-medium">{metrics.n_training_samples}</span></div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Classification Performance</CardTitle></CardHeader>
        <CardContent className="grid gap-3 text-sm md:grid-cols-2">
          <div>Accuracy: <span className="font-medium">{pct(metrics.test_accuracy)}</span></div>
          <div>Macro F1: <span className="font-medium">{pct(metrics.macro_f1)}</span></div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Per-Class Metrics</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          {Object.entries(metrics.per_class || {}).map(([label, values]) => (
            <div key={label} className="rounded border p-3">
              <div className="mb-2 flex items-center justify-between"><Badge variant="outline">{label}</Badge></div>
              <div className="grid grid-cols-3 gap-2 text-sm">
                <div>Precision: <span className="font-medium">{pct(values.precision)}</span></div>
                <div>Recall: <span className="font-medium">{pct(values.recall)}</span></div>
                <div>F1: <span className="font-medium">{pct(values.f1)}</span></div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Confusion Matrix</CardTitle></CardHeader>
        <CardContent>
          {metrics.confusion_matrix?.length ? (
            <div className="overflow-x-auto">
              {/* Column header labels */}
              <div className="mb-1 ml-16 grid gap-1" style={{ gridTemplateColumns: `repeat(${metrics.confusion_matrix[0].length}, minmax(0, 1fr))` }}>
                {['high', 'medium', 'low'].slice(0, metrics.confusion_matrix[0].length).map((label) => (
                  <div key={label} className="text-center text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                    {label}
                  </div>
                ))}
              </div>
              {/* Row labels + cells */}
              {metrics.confusion_matrix.map((row: number[], rowIdx: number) => {
                const rowLabel = ['high', 'medium', 'low'][rowIdx] ?? `Class ${rowIdx}`;
                const maxVal = Math.max(...metrics.confusion_matrix.flat());
                return (
                  <div key={rowIdx} className="mb-1 flex items-center gap-1">
                    <div className="w-14 shrink-0 text-right text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                      {rowLabel}
                    </div>
                    <div className="grid flex-1 gap-1" style={{ gridTemplateColumns: `repeat(${row.length}, minmax(0, 1fr))` }}>
                      {row.map((val, colIdx) => {
                        const intensity = maxVal > 0 ? val / maxVal : 0;
                        const bg = rowIdx === colIdx
                          ? `rgba(34,197,94,${0.15 + intensity * 0.65})`   // green diagonal
                          : `rgba(239,68,68,${intensity * 0.55})`;          // red off-diagonal
                        return (
                          <div
                            key={colIdx}
                            className="flex h-12 items-center justify-center rounded text-sm font-bold"
                            style={{ backgroundColor: bg }}
                          >
                            {val}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
              <p className="mt-2 text-xs text-muted-foreground">
                Rows = Actual class · Columns = Predicted class · Diagonal = correct predictions
              </p>
            </div>
          ) : (
            <span className="text-sm text-muted-foreground">No confusion matrix available.</span>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Feature Importances</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          {metrics.top_10_features?.map((feature) => (
            <div key={feature.feature} className="flex items-center justify-between rounded border px-3 py-2 text-sm">
              <span>{feature.display_name}</span>
              <span className="font-mono text-xs text-muted-foreground">{feature.importance.toFixed(6)}</span>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}

function pct(value: number) {
  return `${(value * 100).toFixed(1)}%`
}
