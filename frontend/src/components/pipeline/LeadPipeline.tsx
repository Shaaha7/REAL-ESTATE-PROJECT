import { useState, useEffect } from 'react'
import TopBar from '../layout/TopBar'
import { getSampleLeads, SampleLead } from '../../services/api'
import toast from 'react-hot-toast'

const STAGES = ['new','contacted','qualified','proposal_sent','negotiating','closed','lost']
const STAGE_LABELS: Record<string, string> = {
  new:'🆕 New', contacted:'📞 Contacted', qualified:'✅ Qualified',
  proposal_sent:'📄 Proposal Sent', negotiating:'🤝 Negotiating', closed:'🎉 Closed', won:'✅ Won', lost:'❌ Lost'
}
const STAGE_COLORS: Record<string, string> = {
  new:'border-blue-500/30 bg-blue-500/5', contacted:'border-amber-500/30 bg-amber-500/5',
  qualified:'border-emerald-500/30 bg-emerald-500/5', proposal_sent:'border-purple-500/30 bg-purple-500/5',
  negotiating:'border-orange-500/30 bg-orange-500/5', closed:'border-emerald-600/50 bg-emerald-600/10',
  won:'border-emerald-600/50 bg-emerald-600/10', lost:'border-red-500/30 bg-red-500/5'
}
const TIER_DOT: Record<string, string> = { HOT:'bg-red-400', WARM:'bg-amber-400', COLD:'bg-blue-400' }

export default function LeadPipeline() {
  const [leads, setLeads] = useState<SampleLead[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    getSampleLeads().then(r => setLeads(r.data.leads))
      .catch(() => toast.error('Could not load leads'))
      .finally(() => setLoading(false))
  }, [])

  const filtered = leads.filter(l =>
    !search || l.client_name.toLowerCase().includes(search.toLowerCase()) || l.location_preference.toLowerCase().includes(search.toLowerCase())
  )

  const byStage = (stage: string) => filtered.filter(l => l.status === stage || (stage === 'new' && !STAGES.includes(l.status)))

  const moveStage = (lead: SampleLead, newStage: string) => {
    setLeads(prev => prev.map(l => l.lead_id === lead.lead_id ? { ...l, status: newStage } : l))
    toast.success(`${lead.client_name} → ${STAGE_LABELS[newStage]}`)
  }

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" /></div>

  return (
    <div>
      <TopBar title="Lead Pipeline" subtitle="200 leads across all stages — drag to move between stages" />
      <div className="mb-6 flex items-center gap-4">
        <input className="input max-w-sm" placeholder="Search leads…" value={search} onChange={e => setSearch(e.target.value)} />
        <div className="flex gap-2 text-xs text-slate-500">
          {Object.entries(TIER_DOT).map(([tier, color]) => (
            <span key={tier} className="flex items-center gap-1">
              <span className={`w-2 h-2 rounded-full ${color}`} />{tier}
            </span>
          ))}
        </div>
      </div>
      <div className="flex gap-4 overflow-x-auto pb-4">
        {STAGES.map(stage => {
          const stageleads = byStage(stage)
          return (
            <div key={stage} className="flex-shrink-0 w-56">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-400">{STAGE_LABELS[stage] || stage}</span>
                <span className="text-xs bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded-full">{stageleads.length}</span>
              </div>
              <div className="space-y-2 min-h-32">
                {stageleads.slice(0, 8).map(lead => (
                  <div key={lead.lead_id} className={`p-2.5 rounded-xl border ${STAGE_COLORS[stage] || STAGE_COLORS.new} cursor-pointer hover:opacity-80 transition-opacity`}>
                    <div className="flex items-center gap-1.5 mb-1">
                      <span className={`w-2 h-2 rounded-full flex-shrink-0 ${TIER_DOT[lead.tier] || TIER_DOT.COLD}`} />
                      <span className="text-xs font-medium text-white truncate">{lead.client_name}</span>
                    </div>
                    <div className="text-xs text-slate-500 truncate">{lead.location_preference || 'Location TBC'}</div>
                    <div className="text-xs text-slate-400 mt-1">AED {(lead.budget_aed/1_000_000).toFixed(1)}M</div>
                    <div className="flex gap-1 mt-2 flex-wrap">
                      {STAGES.filter(s => s !== stage && s !== 'lost').slice(0, 2).map(s => (
                        <button key={s} onClick={() => moveStage(lead, s)}
                          className="text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 px-1.5 py-0.5 rounded transition-colors">
                          → {s.replace('_', ' ')}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
                {stageleads.length > 8 && <div className="text-xs text-slate-500 text-center py-1">+{stageleads.length - 8} more</div>}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
