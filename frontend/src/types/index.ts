export interface Receipt {
  id: string
  userId: string
  merchantName: string
  date: string
  totalAmount: number
  category: string
  lineItems: LineItem[]
  imageUrl: string
  createdAt: Date
  updatedAt: Date
}

export interface LineItem {
  description: string
  quantity: number
  price: number
  amount: number
}

export interface Budget {
  id: string
  userId: string
  category: string
  monthlyLimit: number
  currentSpending: number
  alertThreshold: number
  createdAt: Date
}

export interface SpendingSummary {
  totalSpending: number
  categoryBreakdown: CategorySpending[]
  monthlyTrend: MonthlyData[]
  topMerchants: MerchantSpending[]
}

export interface CategorySpending {
  category: string
  amount: number
  percentage: number
  transactionCount: number
}

export interface MonthlyData {
  month: string
  amount: number
}

export interface MerchantSpending {
  merchant: string
  amount: number
  transactionCount: number
}

export type Category =
  | 'Food & Dining'
  | 'Groceries'
  | 'Transportation'
  | 'Entertainment'
  | 'Shopping'
  | 'Healthcare'
  | 'Utilities'
  | 'Travel'
  | 'Other'
