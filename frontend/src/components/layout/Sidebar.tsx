/**
 * UPDATED Sidebar.tsx — adds links for all new pages
 * Replace your existing frontend/src/components/layout/Sidebar.tsx
 */
import { NavLink } from 'react-router-dom'

const nav = [
  { to: '/',                    label: 'Dashboard',           icon: '📊', section: '' },
  { to: '/leads',               label: 'Score a Lead',        icon: '🎯', section: 'LEADS' },
  { to: '/leads/list',          label: 'All Leads (200)',      icon: '👥', section: '' },
  { to: '/leads/pipeline',      label: 'Lead Pipeline',       icon: '🔄', section: '' },
  { to: '/properties',          label: 'Properties',          icon: '🏠', section: 'PROPERTIES' },
  { to: '/properties/compare',  label: 'Compare Properties',  icon: '⚖️', section: '' },
  { to: '/properties/valuate',  label: 'Property Valuation',  icon: '💰', section: '' },
  { to: '/rag',                 label: 'Knowledge Base',      icon: '📚', section: 'AI TOOLS' },
  { to: '/agent',               label: 'AI Agent Chat',       icon: '🤖', section: '' },
  { to: '/tools/mortgage',      label: 'Mortgage Calculator', icon: '🏦', section: '' },
  { to: '/evaluation',          label: 'RAGAS Evaluation',    icon: '🧪', section: 'SYSTEM' },
]

export default function Sidebar() {
  let lastSection = ''
  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-screen fixed left-0 top-0 z-40">
      <div className="p-6 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-600 to-brand-800 flex items-center justify-center text-white font-black text-lg">P</div>
          <div>
            <div className="font-bold text-white">PropAI</div>
            <div className="text-xs text-slate-400">Real Estate AI Platform</div>
          </div>
        </div>
      </div>
      <nav className="flex-1 p-4 space-y-0.5 overflow-y-auto">
        {nav.map(({ to, label, icon, section }) => {
          const showSection = section && section !== lastSection
          if (showSection) lastSection = section
          return (
            <div key={to}>
              {showSection && (
                <div className="text-xs text-slate-600 font-semibold px-3 pt-4 pb-1 uppercase tracking-wider">{section}</div>
              )}
              <NavLink to={to} end={to === '/' || to === '/leads' || to === '/properties'}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                    isActive ? 'bg-brand-600 text-white shadow-lg' : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800'
                  }`}>
                <span className="text-base">{icon}</span>
                {label}
              </NavLink>
            </div>
          )
        })}
      </nav>
      <div className="p-4 border-t border-slate-800">
        <div className="text-xs text-slate-500 text-center">Gemini 1.5 Flash + LangChain</div>
        <div className="text-xs text-slate-600 text-center mt-0.5">FAISS · XGBoost · SHAP · RAGAS</div>
      </div>
    </aside>
  )
}
