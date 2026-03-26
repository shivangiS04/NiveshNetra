export interface Transaction {
  date: string
  type: string
  amount: number
  units: number
  nav: number
  balanceUnits: number
}

export interface FundResult {
  fundName: string
  folioNumber: string
  totalInvested: number
  currentValue: number
  xirr: number | null
  absoluteReturn: number
  category: string
  benchmark: string
  benchmarkXirr: number | null
  expenseRatio: number | null
  expenseDragAnnual: number
}

export interface OverlapResult {
  fundA: string
  fundB: string
  sharedStocks: string[]
  overlapPct: number
}

export interface RebalancingAction {
  type: 'exit' | 'reduce' | 'switch' | 'enter' | 'action'
  fund: string
  detail: string
  impact: string
}

export interface HealthScoreDimension {
  label: string
  score: number
  insight: string
}

export interface AnalysisResponse {
  funds: FundResult[]
  totalInvested: number
  totalCurrentValue: number
  portfolioXirr: number | null
  absoluteReturn: number
  warnings: string[]
  overlaps: OverlapResult[]
  totalExpenseDragAnnual: number
  rebalancingPlan: string
  rebalancingActions: RebalancingAction[]
  moneyHealthScore: number
  moneyHealthDimensions: HealthScoreDimension[]
}

export interface ApiError {
  error: string
  detail?: string
}

// FIRE Planner types
export interface FireChartPoint {
  year: number
  projected: number | null
  required: number | null
}

export interface AssetAllocation {
  decade: string
  equity: number
  debt: number
}

export interface FirePlanResponse {
  age: number
  riskAppetite: string
  annualReturn: number
  yearsToRetirement: number
  annualExpensesNow: number
  annualExpensesAtRetirement: number
  targetCorpus: number
  projectedCorpusAtRetirement: number
  fireDate: string
  fireAge: number | null
  onTrack: boolean
  yearsEarly: number
  additionalSipNeeded: number
  chartData: FireChartPoint[]
  assetAllocation: AssetAllocation[]
  aiSummary: string
}

// Tax Wizard types
export interface TaxRegimeDetail {
  hraExemption?: number
  standardDeduction: number
  deduction80C?: number
  deduction80D?: number
  deduction24B?: number
  deduction80CCD2?: number
  totalDeductions?: number
  taxableIncome: number
  taxBeforeCess: number
  cess: number
  totalTax: number
}

export interface MissingDeduction {
  section: string
  gap: number
  potentialSaving: number
  message: string
}

export interface TaxRecommendation {
  name: string
  maxBenefit: number
  section: string
  lockIn: string
  risk: string
  taxSaving: number
  alreadyCovered: boolean
}

export interface TaxPlanResponse {
  grossIncome: number
  oldRegime: TaxRegimeDetail
  newRegime: TaxRegimeDetail
  winner: 'old' | 'new' | 'tie'
  savings: number
  missingDeductions: MissingDeduction[]
  recommendations: TaxRecommendation[]
  aiSummary: string
}
