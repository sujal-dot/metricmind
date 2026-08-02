'use client';

import React from 'react';
import { Clock, Database, CheckCircle2, FileText, FileSpreadsheet, Download } from 'lucide-react';

interface DashboardFooterBarProps {
  lastUpdatedText?: string;
  totalRecordsFormatted?: string;
  onExportCsv?: () => void;
  onExportExcel?: () => void;
  onExportPdf?: () => void;
}

export default function DashboardFooterBar({
  lastUpdatedText = 'Just now',
  totalRecordsFormatted = '9,994',
  onExportCsv,
  onExportExcel,
  onExportPdf,
}: DashboardFooterBarProps) {
  return (
    <footer className="mt-8 pt-4 pb-6 border-t border-gray-200 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-gray-500">
      {/* Left side: System & Data Status Indicators */}
      <div className="flex flex-wrap items-center gap-6">
        <div className="flex items-center gap-1.5">
          <Clock className="w-4 h-4 text-gray-400" />
          <span>
            Last Updated: <strong className="font-semibold text-gray-700">{lastUpdatedText}</strong>
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <Database className="w-4 h-4 text-gray-400" />
          <span>
            Records: <strong className="font-semibold text-gray-700">{totalRecordsFormatted}</strong>
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>
            Cube API: <strong className="font-semibold text-emerald-700">Connected</strong>
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>
            Semantic Layer: <strong className="font-semibold text-emerald-700">Healthy</strong>
          </span>
        </div>
      </div>

      {/* Right side: Export Action Buttons */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onExportPdf}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100 transition-colors font-medium text-xs"
        >
          <FileText className="w-3.5 h-3.5" />
          PDF
        </button>

        <button
          type="button"
          onClick={onExportExcel}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 transition-colors font-medium text-xs"
        >
          <FileSpreadsheet className="w-3.5 h-3.5" />
          Excel
        </button>

        <button
          type="button"
          onClick={onExportCsv}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors font-medium text-xs"
        >
          <Download className="w-3.5 h-3.5" />
          CSV
        </button>
      </div>
    </footer>
  );
}
