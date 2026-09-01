'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  ChevronLeft, ChevronRight, Maximize, Minimize, Download,
  Loader2, Presentation as PresentationIcon,
} from 'lucide-react';
import { reportEngineService, type SlideData } from '@/services/reports/reportEngineService';
import { SlideChart } from '@/components/reports/SlideChart';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';

interface PresentationViewerProps {
  reportId: string;
  className?: string;
}

export function PresentationViewer({ reportId, className }: PresentationViewerProps) {
  const [slides, setSlides] = useState<SlideData[]>([]);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [loading, setLoading] = useState(true);
  const [fullscreen, setFullscreen] = useState(false);
  const [title, setTitle] = useState('');

  const loadPresentation = useCallback(async () => {
    try {
      const data = await reportEngineService.getPresentation(reportId);
      setSlides(data.slides);
      setTitle(data.title);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [reportId]);

  useEffect(() => {
    loadPresentation();
  }, [loadPresentation]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') setCurrentSlide((s) => Math.min(s + 1, slides.length - 1));
      if (e.key === 'ArrowLeft') setCurrentSlide((s) => Math.max(s - 1, 0));
      if (e.key === 'Escape') setFullscreen(false);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [slides.length]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (slides.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <PresentationIcon className="mb-4 h-12 w-12 text-muted-foreground" />
        <p className="text-muted-foreground">No slides available</p>
      </div>
    );
  }

  const slide = slides[currentSlide];

  const containerClass = cn(
    'bg-white dark:bg-slate-900',
    fullscreen && 'fixed inset-0 z-50 flex flex-col',
    !fullscreen && 'rounded-xl border-2 shadow-lg',
    className,
  );

  const slideClass = cn(
    'relative flex flex-col items-center justify-center overflow-hidden',
    fullscreen ? 'flex-1' : 'aspect-video',
  );

  return (
    <div className={containerClass}>
      {/* Slide content */}
      <div className={slideClass}>
        {/* Title slide */}
        {slide.layout === 'title' && (
          <div className="flex h-full w-full flex-col items-center justify-center bg-gradient-to-br from-slate-800 to-slate-900 text-white">
            <h1 className="px-8 text-center text-3xl font-bold md:text-4xl">{slide.title}</h1>
            {slide.subtitle && (
              <p className="mt-4 text-lg text-slate-300">{slide.subtitle}</p>
            )}
          </div>
        )}

        {/* Bullet slide */}
        {slide.layout === 'bullets' && (
          <div className="w-full px-12 py-8">
            <h2 className="mb-6 text-2xl font-bold text-slate-900 dark:text-slate-100">{slide.title}</h2>
            <div className="space-y-3">
              {slide.content?.split('\n').filter(Boolean).map((line, i) => (
                <div key={i} className="flex items-start gap-3">
                  <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-primary" />
                  <p className="text-base text-slate-700 dark:text-slate-300">{line}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* KPI slide */}
        {slide.layout === 'kpi' && (
          <div className="w-full px-12 py-8">
            <h2 className="mb-6 text-2xl font-bold text-slate-900 dark:text-slate-100">{slide.title}</h2>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              {slide.kpis?.map((kpi, i) => (
                <div key={i} className="rounded-xl border-2 p-4 text-center">
                  <p className="text-xs uppercase text-muted-foreground">{kpi.label}</p>
                  <p className="mt-2 text-2xl font-bold text-primary">{kpi.value}</p>
                  {kpi.trend_value && (
                    <p className={cn(
                      'mt-1 text-xs',
                      kpi.trend === 'up' ? 'text-green-600' : kpi.trend === 'down' ? 'text-red-600' : 'text-muted-foreground'
                    )}>
                      {kpi.trend_value}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Chart slide */}
        {slide.layout === 'chart' && (
          <div className="w-full px-12 py-8">
            <h2 className="mb-6 text-2xl font-bold text-slate-900 dark:text-slate-100">{slide.title}</h2>
            <div className="rounded-xl border-2 border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800">
              <SlideChart
                chartType={slide.chart_type || 'bar'}
                data={slide.chart_data || []}
                xAxis={slide.x_axis}
                yAxis={slide.y_axis}
                height={fullscreen ? 400 : 280}
              />
            </div>
          </div>
        )}

        {/* Table slide */}
        {slide.layout === 'table' && (
          <div className="w-full px-12 py-8">
            <h2 className="mb-6 text-2xl font-bold text-slate-900 dark:text-slate-100">{slide.title}</h2>
            <div className="overflow-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b-2 border-slate-200 dark:border-slate-700">
                    {slide.columns?.map((col, i) => (
                      <th key={i} className="px-3 py-2 text-left font-semibold text-slate-700 dark:text-slate-300">{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {slide.rows?.map((row, i) => (
                    <tr key={i} className="border-b border-slate-100 dark:border-slate-800">
                      {Array.isArray(row) && row.map((cell, j) => (
                        <td key={j} className="px-3 py-2 text-slate-600 dark:text-slate-400">{String(cell)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between border-t px-4 py-2">
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => setCurrentSlide((s) => Math.max(0, s - 1))}
            disabled={currentSlide === 0}
            className="gap-1"
          >
            <ChevronLeft size={16} /> Prev
          </Button>
          <span className="text-xs text-muted-foreground">
            {currentSlide + 1} / {slides.length}
          </span>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setCurrentSlide((s) => Math.min(slides.length - 1, s + 1))}
            disabled={currentSlide === slides.length - 1}
            className="gap-1"
          >
            Next <ChevronRight size={16} />
          </Button>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => setFullscreen(!fullscreen)}
            className="gap-1"
          >
            {fullscreen ? <Minimize size={14} /> : <Maximize size={14} />}
            {fullscreen ? 'Exit' : 'Fullscreen'}
          </Button>
          <a
            href={reportEngineService.exportPresentationUrl(reportId, 'pptx')}
            download
          >
            <Button size="sm" className="gap-1">
              <Download size={14} /> PPTX
            </Button>
          </a>
        </div>
      </div>

      {/* Slide thumbnails */}
      {!fullscreen && (
        <div className="flex gap-2 overflow-x-auto border-t px-4 py-2">
          {slides.map((s, i) => (
            <button
              key={i}
              onClick={() => setCurrentSlide(i)}
              className={cn(
                'flex h-12 w-20 shrink-0 items-center justify-center rounded border-2 text-xs font-medium transition-all',
                i === currentSlide
                  ? 'border-primary bg-primary/5 text-primary'
                  : 'border-slate-200 text-slate-400 hover:border-slate-300 dark:border-slate-700'
              )}
            >
              {i + 1}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
