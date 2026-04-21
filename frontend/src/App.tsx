/**
 * UPDATED App.tsx — adds 4 new routes
 * Replace your existing frontend/src/App.tsx with this file
 */
import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Dashboard from './components/dashboard/Dashboard'
import LeadScoring from './components/leads/LeadScoring'
import LeadsList from './components/leads/LeadsList'
import Properties from './components/properties/Properties'
import KnowledgeBase from './components/rag/KnowledgeBase'
import AgentChat from './components/rag/AgentChat'
import Evaluation from './components/evaluation/Evaluation'
// ── NEW IMPORTS ────────────────────────────────────────────────────────────────
import MortgageCalculator from './components/calculator/MortgageCalculator'
import PropertyComparison from './components/comparison/PropertyComparison'
import Valuation from './components/comparison/Valuation'
import LeadPipeline from './components/pipeline/LeadPipeline'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="leads" element={<LeadScoring />} />
        <Route path="leads/list" element={<LeadsList />} />
        <Route path="leads/pipeline" element={<LeadPipeline />} />   {/* NEW */}
        <Route path="properties" element={<Properties />} />
        <Route path="properties/compare" element={<PropertyComparison />} />  {/* NEW */}
        <Route path="properties/valuate" element={<Valuation />} />           {/* NEW */}
        <Route path="rag" element={<KnowledgeBase />} />
        <Route path="agent" element={<AgentChat />} />
        <Route path="evaluation" element={<Evaluation />} />
        <Route path="tools/mortgage" element={<MortgageCalculator />} />      {/* NEW */}
      </Route>
    </Routes>
  )
}
