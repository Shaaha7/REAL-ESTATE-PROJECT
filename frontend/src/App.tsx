import { Suspense, lazy } from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'

const Dashboard = lazy(() => import('./components/dashboard/Dashboard'))
const LeadScoring = lazy(() => import('./components/leads/LeadScoring'))
const LeadsList = lazy(() => import('./components/leads/LeadsList'))
const LeadPipeline = lazy(() => import('./components/pipeline/LeadPipeline'))
const Properties = lazy(() => import('./components/properties/Properties'))
const PropertyComparison = lazy(() => import('./components/comparison/PropertyComparison'))
const Valuation = lazy(() => import('./components/comparison/Valuation'))
const KnowledgeBase = lazy(() => import('./components/rag/KnowledgeBase'))
const AgentChat = lazy(() => import('./components/rag/AgentChat'))
const Evaluation = lazy(() => import('./components/evaluation/Evaluation'))
const MortgageCalculator = lazy(() => import('./components/calculator/MortgageCalculator'))

const RouteFallback = () => (
  <div className="flex items-center justify-center h-64">
    <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
  </div>
)

export default function App() {
  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="leads" element={<LeadScoring />} />
          <Route path="leads/list" element={<LeadsList />} />
          <Route path="leads/pipeline" element={<LeadPipeline />} />
          <Route path="properties" element={<Properties />} />
          <Route path="properties/compare" element={<PropertyComparison />} />
          <Route path="properties/valuate" element={<Valuation />} />
          <Route path="rag" element={<KnowledgeBase />} />
          <Route path="agent" element={<AgentChat />} />
          <Route path="evaluation" element={<Evaluation />} />
          <Route path="tools/mortgage" element={<MortgageCalculator />} />
        </Route>
      </Routes>
    </Suspense>
  )
}
