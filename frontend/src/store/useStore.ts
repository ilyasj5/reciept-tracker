import { create } from 'zustand'
import { Receipt, Budget, SpendingSummary } from '@/types'

interface Store {
  receipts: Receipt[]
  budgets: Budget[]
  spendingSummary: SpendingSummary | null
  loading: boolean
  error: string | null

  setReceipts: (receipts: Receipt[]) => void
  addReceipt: (receipt: Receipt) => void
  setBudgets: (budgets: Budget[]) => void
  setSpendingSummary: (summary: SpendingSummary) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useStore = create<Store>((set) => ({
  receipts: [],
  budgets: [],
  spendingSummary: null,
  loading: false,
  error: null,

  setReceipts: (receipts) => set({ receipts }),
  addReceipt: (receipt) => set((state) => ({
    receipts: [receipt, ...state.receipts]
  })),
  setBudgets: (budgets) => set({ budgets }),
  setSpendingSummary: (summary) => set({ spendingSummary: summary }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}))
