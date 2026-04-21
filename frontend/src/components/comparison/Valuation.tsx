import { useState } from 'react'
import TopBar from '../layout/TopBar'
import api from '../../services/api'
import toast from 'react-hot-toast'

const fmt = (n: number) => `AED ${Math.round(n).toLocaleString()}`
const fmtM = (n: number) => n >= 1_000_000 ? `AED ${(n/1_000_000).toFixed(2)}M` : fmt(n)

export default function Valuation() {
  const [form, setForm] = useState({
    property_type: 'apartment', location: 'Dubai Marina',
    bedrooms: 2, area_sqft: 1200, floor: 15,
    view: 'sea', condition: 'good', furnished: false, asking_price_aed: 0
  })
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const up = (k: string, v: any) => setForm(p => ({ ...p, [k]: v }))

  const valuate = async () => {
    setLoading(true)
    try {
      const r = await api.post('/tools/valuate', form)
      setResult(r.data)
    } catch { toast.error('Valuation failed') }
    finally { setLoading(false) }
  }

  const fair = result && form.asking_price_aed > 0
    ? form.asking_price_aed <= result.estimated_value_aed * 1.05 && form.asking_price_aed >= result.estimated_value_aed * 0.95
    : null

  return (
    <div>
      <TopBar title="Property Valuation" subtitle="AI-powered market value estimate using area benchmarks and DLD comparables" />
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        <div className="card space-y-4">
          <h2 className="font-semibold text-white text-sm">Property Details</h2>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Type</label>
              <select className="select" value={form.property_type} onChange={e => up('property_type', e.target.value)}>
                {['apartment','villa','townhouse','penthouse','studio'].map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase()+t.slice(1)}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Location / Area</label>
              <input className="input" value={form.location} onChange={e => up('location', e.target.value)} placeholder="Dubai Marina, JVC…" />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Bedrooms</label>
              <input type="number" className="input" value={form.bedrooms} min={0} max={10} onChange={e => up('bedrooms', +e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Size (sqft)</label>
              <input type="number" className="input" value={form.area_sqft} onChange={e => up('area_sqft', +e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Floor Number</label>
              <input type="number" className="input" value={form.floor} min={0} onChange={e => up('floor', +e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">View</label>
              <select className="select" value={form.view} onChange={e => up('view', e.target.value)}>
                {['sea','burj khalifa','golf','marina','canal','city','community','street'].map(v => <option key={v} value={v}>{v.charAt(0).toUpperCase()+v.slice(1)}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Condition</label>
              <select className="select" value={form.condition} onChange={e => up('condition', e.target.value)}>
                {[['new','Brand New'],['good','Good'],['needs_work','Needs Work']].map(([v,l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Asking Price (AED, optional)</label>
              <input type="number" className="input" value={form.asking_price_aed || ''} onChange={e => up('asking_price_aed', +e.target.value)} placeholder="0 = not listed" />
            </div>
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
            <input type="checkbox" checked={form.furnished} onChange={e => up('furnished', e.target.checked)} className="accent-brand-500" />
            Furnished
          </label>
          <button className="btn-primary w-full justify-center" onClick={valuate} disabled={loading}>
            {loading ? <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" /> : '🏠'}
            Get Valuation
          </button>
        </div>

        {result ? (
          <div className="space-y-4">
            <div className="card border border-brand-700/50">
              <div className="text-xs text-slate-400 mb-1">Estimated Market Value</div>
              <div className="text-3xl font-black text-white mb-1">{fmtM(result.estimated_value_aed)}</div>
              <div className="text-slate-400 text-sm">Range: {fmtM(result.value_range_low_aed)} – {fmtM(result.value_range_high_aed)}</div>
              <div className="text-slate-400 text-sm mt-1">AED {Math.round(result.price_per_sqft).toLocaleString()}/sqft</div>
            </div>

            {form.asking_price_aed > 0 && (
              <div className={`card border ${fair ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-red-500/30 bg-red-500/5'}`}>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-white">Asking Price Assessment</span>
                  <span className={`text-sm font-bold ${fair ? 'text-emerald-400' : 'text-red-400'}`}>{fair ? '✓ Fair Price' : '⚠ Review Price'}</span>
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  Asking: {fmtM(form.asking_price_aed)} | Estimated: {fmtM(result.estimated_value_aed)}
                  {' | '}Difference: {((form.asking_price_aed / result.estimated_value_aed - 1) * 100).toFixed(1)}%
                </div>
              </div>
            )}

            <div className="card">
              <h3 className="font-semibold text-white text-sm mb-2">Recommendation</h3>
              <p className="text-slate-300 text-sm leading-relaxed">{result.recommendation}</p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {result.value_drivers?.length > 0 && (
                <div className="card">
                  <h3 className="font-semibold text-white text-xs mb-2">Value Drivers ▲</h3>
                  {result.value_drivers.map((d: string, i: number) => <div key={i} className="text-xs text-emerald-400 py-0.5">✓ {d}</div>)}
                </div>
              )}
              {result.value_detractors?.length > 0 && (
                <div className="card">
                  <h3 className="font-semibold text-white text-xs mb-2">Detractors ▼</h3>
                  {result.value_detractors.map((d: string, i: number) => <div key={i} className="text-xs text-red-400 py-0.5">✗ {d}</div>)}
                </div>
              )}
            </div>
            <div className="card">
              <h3 className="font-semibold text-white text-xs mb-2">Comparable Areas</h3>
              {result.comparable_areas?.map((a: string, i: number) => <div key={i} className="text-xs text-slate-400 py-0.5">• {a}</div>)}
            </div>
          </div>
        ) : (
          <div className="card flex flex-col items-center justify-center min-h-64 text-center">
            <div className="text-5xl mb-4">💰</div>
            <p className="text-slate-400 text-sm">Enter property details to get an AI-powered market value estimate based on Dubai area benchmarks and recent DLD transactions.</p>
          </div>
        )}
      </div>
    </div>
  )
}
