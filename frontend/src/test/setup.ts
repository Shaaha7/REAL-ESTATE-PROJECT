import '@testing-library/jest-dom/vitest'

// jsdom doesn't implement ResizeObserver; recharts' ResponsiveContainer needs
// it to measure its container. Chart dimensions aren't under test, so a
// no-op stub is enough - this just stops it from throwing.
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
;(globalThis as any).ResizeObserver = ResizeObserverStub
