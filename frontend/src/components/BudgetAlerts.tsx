'use client'

import { useEffect, useState } from 'react'
import { db } from '@/lib/firebase'
import { collection, query, where, getDocs } from 'firebase/firestore'
import { Budget } from '@/types'
import { AlertTriangle, TrendingUp } from 'lucide-react'

interface BudgetAlertsProps {
  userId: string
}

export default function BudgetAlerts({ userId }: BudgetAlertsProps) {
  const [alerts, setAlerts] = useState<Budget[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchBudgets = async () => {
      try {
        const budgetsRef = collection(db, 'budgets')
        const q = query(budgetsRef, where('userId', '==', userId))
        const snapshot = await getDocs(q)

        const budgetsData = snapshot.docs.map((doc) => ({
          id: doc.id,
          ...doc.data(),
        })) as Budget[]

        // Filter for budgets exceeding alert threshold
        const exceededBudgets = budgetsData.filter(
          (budget) => (budget.currentSpending / budget.monthlyLimit) * 100 >= budget.alertThreshold
        )

        setAlerts(exceededBudgets)
      } catch (error) {
        console.error('Error fetching budgets:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchBudgets()
  }, [userId])

  if (loading || alerts.length === 0) {
    return null
  }

  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
      <div className="flex items-start space-x-3">
        <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-yellow-900 mb-2">Budget Alerts</h3>
          <div className="space-y-2">
            {alerts.map((budget) => {
              const percentage = (budget.currentSpending / budget.monthlyLimit) * 100
              return (
                <div key={budget.id} className="text-sm text-yellow-800">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium">{budget.category}</span>
                    <span className="font-semibold">{percentage.toFixed(0)}% used</span>
                  </div>
                  <div className="w-full bg-yellow-200 rounded-full h-2">
                    <div
                      className="bg-yellow-600 h-2 rounded-full transition-all"
                      style={{ width: `${Math.min(percentage, 100)}%` }}
                    />
                  </div>
                  <p className="text-xs mt-1">
                    ${budget.currentSpending.toFixed(2)} of ${budget.monthlyLimit.toFixed(2)}
                  </p>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
