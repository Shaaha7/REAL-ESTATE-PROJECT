import { useState } from 'react'
import TopBar from '../layout/TopBar'
import toast from 'react-hot-toast'
import api from '../../services/api'

const fmt = (n: number) => `AED ${Math.round(n).toLocaleString()}`
const fmtM = (n: number) => n >= 1_000_000 ? `AED ${(n/1_000_000).toFixed(2)}M` : fmt(n)

export default function MortgageCalculator() {
  const [form, setForm] = useState({
    property_price_aed: 2000000, monthly_income_aed: 30000,
    existing_debts_aed: 0, down_payment_pct: 25,
    interest_rate_pct: 4.5, tenure_years: 25,
    is_uae_national: false, is_resident: true
  })
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const up = (k: string, v: any) => setForm(p => ({ ...p, [k]: v }))

  const calculate = async () => {
    setLoading(true)
    try {
      const r = await api.post('/tools/mortgage', form)
      setResult(r.data)
    } catch { toast.error('Calculation failed') }
    finally { setLoading(false) }
  }

  const dbr = result?.debt_burden_ratio_pct
  const dbrOk = typeof dbr === 'number' && dbr <= 50

  return (
    <div>
      <TopBar title="Mortgage Calculator" subtitle="UAE Central Bank rules · LTV limits · Bank recommendations" />
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        <div className="card space-y-4">
          <h2 className="font-semibold text-white text-sm">Property & Loan Details</h2>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Property Price (AED)</label>
              <input type="number" className="input" value={form.property_price_aed} onChange={e => up('property_price_aed', +e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Monthly Income (AED)</label>
              <input type="number" className="input" value={form.monthly_income_aed} onChange={e => up('monthly_income_aed', +e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Existing Monthly Debts (AED)</label>
              <input type="number" className="input" value={form.existing_debts_aed} onChange={e => up('existing_debts_aed', +e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Down Payment %</label>
              <input type="number" className="input" value={form.down_payment_pct} min={20} max={100} onChange={e => up('down_payment_pct', +e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Interest Rate %</label>
              <input type="number" className="input" value={form.interest_rate_pct} step={0.1} onChange={e => up('interest_rate_pct', +e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Tenure (years)</label>
              <input type="number" className="input" value={form.tenure_years} min={5} max={30} onChange={e => up('tenure_years', +e.target.value)} />
            </div>
          </div>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
              <input type="checkbox" checked={form.is_uae_national} onChange={e => up('is_uae_national', e.target.checked)} className="accent-brand-500" />
              UAE National
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
              <input type="checkbox" checked={form.is_resident} onChange={e => up('is_resident', e.target.checked)} className="accent-brand-500" />
              UAE Resident
            </label>
          </div>
          <button className="btn-primary w-full justify-center" onClick={calculate} disabled={loading}>
            {loading ? <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" /> : '🧮'}
            Calculate Mortgage
          </button>
        </div>

        {result ? (
          <div className="space-y-4">
            <div className="card border border-brand-700/50">
              <div className="text-3xl font-black text-white mb-1">{fmt(result.monthly_payment_aed)}<span className="text-sm text-slate-400">/month</span></div>
              <div className="text-slate-400 text-sm">at {result.interest_rate_pct}% for {result.tenure_years} years</div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {[
                ['Down Payment', fmtM(result.down_payment_aed), `${result.down_payment_pct}% of price`],
                ['Loan Amount', fmtM(result.loan_amount_aed), `${100 - result.down_payment_pct}% LTV`],
                ['Total Repayment', fmtM(result.total_repayment_aed), 'over full term'],
                ['Total Interest', fmtM(result.total_interest_aed), 'cost of borrowing'],
              ].map(([label, value, sub]) => (
                <div key={label as string} className="card py-3">
                  <div className="text-xs text-slate-500 mb-1">{label}</div>
                  <div className="font-bold text-white text-sm">{value}</div>
                  <div className="text-xs text-slate-500">{sub}</div>
                </div>
              ))}
            </div>
            <div className={`card border ${dbrOk ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-red-500/30 bg-red-500/5'}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold text-white">Debt Burden Ratio (DBR)</span>
                <span className={`text-sm font-bold ${dbrOk ? 'text-emerald-400' : 'text-red-400'}`}>{typeof dbr === 'number' ? `${dbr}%` : dbr}</span>
              </div>
              <div className="h-2 bg-slate-800 rounded-full overflow-hidden mb-2">
                <div className={`h-full rounded-full transition-all ${dbrOk ? 'bg-emerald-500' : 'bg-red-500'}`} style={{ width: `${Math.min(typeof dbr === 'number' ? dbr : 0, 100)}%` }} />
              </div>
              <p className="text-xs text-slate-400">UAE Central Bank maximum: 50% | {dbrOk ? '✓ You qualify' : '✗ Exceeds limit — reduce loan or increase income'}</p>
            </div>
            <div className="card">
              <h3 className="font-semibold text-white text-sm mb-3">Total Cash Needed</h3>
              <div className="text-2xl font-bold text-amber-400 mb-3">{fmtM(result.total_cash_needed_aed)}</div>
              {result.closing_costs && Object.entries(result.closing_costs).slice(0, -1).map(([k, v]) => (
                <div key={k} className="flex justify-between text-xs py-1 border-b border-slate-800/50">
                  <span className="text-slate-400 capitalize">{k.replace(/_aed|_/g, ' ')}</span>
                  <span className="text-white">{fmt(v as number)}</span>
                </div>
              ))}
            </div>
            <div className="card">
              <h3 className="font-semibold text-white text-sm mb-2">Recommended Banks</h3>
              {result.recommended_banks?.map((b: string, i: number) => (
                <div key={i} className="text-xs text-slate-400 py-1 border-b border-slate-800/50 last:border-0">🏦 {b}</div>
              ))}
            </div>
          </div>
        ) : (
          <div className="card flex flex-col items-center justify-center min-h-64 text-center">
            <div className="text-5xl mb-4">🏦</div>
            <p className="text-slate-400 text-sm">Fill in the details and click <strong className="text-white">Calculate Mortgage</strong> to see monthly payments, DBR ratio, closing costs, and bank recommendations.</p>
          </div>
        )}
      </div>
    </div>
  )
}
