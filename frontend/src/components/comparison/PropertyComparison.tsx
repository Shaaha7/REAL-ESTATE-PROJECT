import { useState } from 'react'
import TopBar from '../layout/TopBar'
import api from '../../services/api'
import toast from 'react-hot-toast'

const PROPERTIES = [
  {id:'P001',label:'P001 — 3BR Villa, Dubai Hills, AED 2.15M'},
  {id:'P002',label:'P002 — 2BR Apt, Dubai Marina, AED 1.35M'},
  {id:'P003',label:'P003 — 1BR Apt, JLT, AED 680K'},
  {id:'P004',label:'P004 — 4BR Townhouse, Arabian Ranches, AED 3.2M'},
  {id:'P005',label:'P005 — Studio, Downtown Dubai, AED 920K'},
  {id:'P006',label:'P006 — 3BR Apt, Business Bay, AED 1.85M'},
  {id:'P007',label:'P007 — 5BR Villa, Palm Jumeirah, AED 8.5M'},
  {id:'P008',label:'P008 — 2BR Townhouse, Mirdif, AED 1.1M'},
  {id:'P009',label:'P009 — 3BR Penthouse, Dubai Marina, AED 4.2M'},
  {id:'P010',label:'P010 — 1BR Apt, JVC, AED 550K'},
]

export default function PropertyComparison() {
  const [selected, setSelected] = useState<string[]>(['P001', 'P002'])
  const [profile, setProfile] = useState('')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const toggle = (id: string) => {
    if (selected.includes(id)) {
      if (selected.length > 2) setSelected(p => p.filter(x => x !== id))
    } else {
      if (selected.length < 3) setSelected(p => [...p, id])
      else toast.error('Maximum 3 properties to compare')
    }
  }

  const compare = async () => {
    if (selected.length < 2) { toast.error('Select at least 2 properties'); return }
    setLoading(true)
    try {
      const r = await api.post('/tools/compare', { property_ids: selected, buyer_profile: profile })
      setResult(r.data)
    } catch { toast.error('Comparison failed') }
    finally { setLoading(false) }
  }

  return (
    <div>
      <TopBar title="Property Comparison" subtitle="Compare up to 3 properties side by side with AI analysis" />
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        <div className="space-y-4">
          <div className="card">
            <h3 className="font-semibold text-white text-sm mb-3">Select Properties (2-3)</h3>
            <div className="space-y-2">
              {PROPERTIES.map(p => (
                <button key={p.id} onClick={() => toggle(p.id)}
                  className={`w-full text-left text-xs p-2.5 rounded-xl border transition-all ${selected.includes(p.id) ? 'border-brand-500 bg-brand-500/10 text-brand-300' : 'border-slate-700 text-slate-400 hover:border-slate-600'}`}>
                  {selected.includes(p.id) && <span className="mr-1.5">✓</span>}
                  {p.label}
                </button>
              ))}
            </div>
          </div>
          <div className="card">
            <label className="text-xs text-slate-400 mb-2 block">Your Profile (optional)</label>
            <textarea className="input h-20 resize-none" placeholder="e.g. investor looking for high yield, family wanting good schools, cash buyer..." value={profile} onChange={e => setProfile(e.target.value)} />
          </div>
          <button className="btn-primary w-full justify-center" onClick={compare} disabled={loading || selected.length < 2}>
            {loading ? <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" /> : '⚡'}
            Compare {selected.length} Properties
          </button>
        </div>

        <div className="xl:col-span-2">
          {result ? (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-3">
                {[
                  {label:'Overall Winner', id:result.winner_overall, color:'text-amber-400', icon:'🏆'},
                  {label:'Best Investment', id:result.winner_investment, color:'text-emerald-400', icon:'📈'},
                  {label:'Best Lifestyle', id:result.winner_lifestyle, color:'text-brand-400', icon:'🌟'},
                ].map(w => (
                  <div key={w.label} className="card text-center">
                    <div className="text-2xl mb-1">{w.icon}</div>
                    <div className={`text-lg font-black ${w.color}`}>{w.id}</div>
                    <div className="text-xs text-slate-500">{w.label}</div>
                  </div>
                ))}
              </div>

              {result.comparison_table && (
                <div className="card overflow-x-auto">
                  <h3 className="font-semibold text-white text-sm mb-3">Side-by-Side Comparison</h3>
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-500">
                        <th className="text-left py-2 pr-4">Metric</th>
                        {selected.map(id => <th key={id} className="text-left py-2 px-3 text-brand-400">{id}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {result.comparison_table.map((row: any, i: number) => (
                        <tr key={i} className="border-b border-slate-800/50">
                          <td className="py-2 pr-4 text-slate-400 font-medium">{row.metric}</td>
                          {selected.map(id => (
                            <td key={id} className="py-2 px-3 text-slate-300">{row.values?.[id] || '—'}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {result.property_verdicts && (
                <div className="grid gap-3" style={{gridTemplateColumns:`repeat(${selected.length},1fr)`}}>
                  {selected.map(id => {
                    const v = result.property_verdicts?.[id]
                    if (!v) return null
                    return (
                      <div key={id} className="card">
                        <div className="font-bold text-brand-400 mb-2">{id}</div>
                        <div className="space-y-1 mb-3">
                          {v.pros?.map((p: string, i: number) => <div key={i} className="text-xs text-emerald-400">✓ {p}</div>)}
                        </div>
                        <div className="space-y-1 mb-3">
                          {v.cons?.map((c: string, i: number) => <div key={i} className="text-xs text-red-400">✗ {c}</div>)}
                        </div>
                        <div className="text-xs text-slate-400 bg-slate-800 rounded-lg p-2">👤 {v.best_for}</div>
                      </div>
                    )
                  })}
                </div>
              )}

              {result.recommendation && (
                <div className="card border border-brand-700/50">
                  <h3 className="font-semibold text-white text-sm mb-2">AI Recommendation</h3>
                  <p className="text-slate-300 text-sm leading-relaxed">{result.recommendation}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="card flex flex-col items-center justify-center min-h-64 text-center">
              <div className="text-5xl mb-4">⚖️</div>
              <p className="text-slate-400 text-sm">Select 2 or 3 properties from the list, optionally describe your profile, then click <strong className="text-white">Compare</strong> for a detailed AI analysis.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
