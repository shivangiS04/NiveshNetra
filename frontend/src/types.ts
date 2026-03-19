export interface Transaction {
  date: string
  type: string
  amount: number
  units: number
  nav: number
  balanceUnits: number
}

export interface FundHolding {
  fundName: string
  folioNumber: string
  isin: string
  transactions: Transaction[]
  currentNav: number
  currentUnits: number
  currentValue: number
  totalInvested: number
}

export interface FundResult {
  fundName: string
  folioNumber: string
  totalInvested: number
  currentValue: number
  xirr: number | null   // e.g. 0.142 = 14.2%; null if unconverged
  absoluteReturn: number
}

export interface AnalysisResponse {
  funds: FundResult[]
  totalInvested: number
  totalCurrentValue: number
  portfolioXirr: number | null
  absoluteReturn: number
  warnings: string[]
}

export interface ApiError {
  error: string
  detail?: string
}
