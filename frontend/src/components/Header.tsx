import React from 'react'
import { Activity, RefreshCw, Zap } from 'lucide-react'

interface HeaderProps {
  demoMode: boolean
  onToggleDemoMode: () => void
  onRefresh: () => void
}

export default function Header({ demoMode, onToggleDemoMode, onRefresh }: HeaderProps) {
  return (
    <header className="sticky top-0 z-50 bg-gray-950/95 backdrop-blur border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Zap className="w-8 h-8 text-blue-400" />
            <div>
              <h1 className="text-2xl font-bold text-white">RiskMesh</h1>
              <p className="text-sm text-gray-400">Real-Time Graph-Based Risk Detection</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Status Badge */}
            <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 rounded-lg">
              <Activity className="w-4 h-4 text-green-400" />
              <span className="text-sm text-gray-300">
                {demoMode ? '🎬 Demo Mode' : '🔴 Live Mode'}
              </span>
            </div>

            {/* Mode Toggle */}
            <button
              onClick={onToggleDemoMode}
              className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm font-medium transition-colors"
            >
              {demoMode ? 'Use Real API' : 'Use Demo'}
            </button>

            {/* Refresh Button */}
            <button
              onClick={onRefresh}
              className="p-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
